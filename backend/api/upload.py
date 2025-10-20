from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import os
import uuid
import hashlib
from datetime import datetime
from db.surrealdb_client import db_client
import traceback
from utils.auth import get_current_user
from utils.config import settings
from workers.video_processor import process_video

router = APIRouter()

# Upload directory: use centralized value from settings so workers and API agree
UPLOAD_DIR = settings.UPLOAD_DIR or os.environ.get('UPLOAD_DIR', '/tmp/uploads')
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except OSError as e:
    # If the configured path is read-only or not writable, fall back to /tmp
    try:
        fallback = '/tmp'
        os.makedirs(fallback, exist_ok=True)
        UPLOAD_DIR = fallback
        print(f"Warning: upload directory not writable, falling back to {fallback}: {e}")
    except Exception as ex:
        raise RuntimeError(f"No writable upload directory available (tried {UPLOAD_DIR} and /tmp): {ex}")

@router.post('/upload')
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form('Untitled'),
    current_user_id: str = Depends(get_current_user)
):
    """
    Upload a video file and create a video record in the database.
    Returns the video_id and playback_url.
    """
    try:
        # Debug: log whether Authorization header was present (don't print token)
        from fastapi import Request
        # FastAPI will provide the Request via dependency injection only if declared; instead, inspect starlette context via UploadFile.
        # As a light-weight check, we look at file._headers if available (starlette UploadFile stores headers)
        try:
            headers = getattr(file, '_headers', None)
            auth_present = False
            if headers:
                # headers is a list of tuples
                for k, v in headers:
                    if k.lower() == 'authorization':
                        auth_present = True
                        break
            print(f"Upload debug: Authorization header present in UploadFile headers: {auth_present}")
        except Exception:
            # Non-fatal; move on
            pass

        # Development-only: allow bypass of auth with ?dev_bypass=1 when not in production
        from fastapi import Request
        request: Request = Request.scope.get('request') if hasattr(Request, 'scope') else None
        # NOTE: Above is a no-op in many FastAPI setups; instead, we fall back to environment flagging.
        if settings.ENVIRONMENT != 'production':
            # If the file object comes from an unauthenticated test (no current_user_id),
            # set a default test user to allow local testing flows.
            if not current_user_id:
                current_user_id = 'user:1'

        # Generate unique filename
        timestamp = int(datetime.utcnow().timestamp())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Read and save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Compute content hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Create CDN URL (for now, just a local path - in production this would be a CDN URL)
        cdn_url = f"/uploads/{unique_filename}"
        
        # Create video record in database. If AI processing is enabled, mark as
        # 'queued' so frontend can show it as 'Under review' / queued while the
        # AI pipeline awaits processing. Otherwise mark as 'active' immediately.
        initial_status = 'queued' if settings.ENABLE_AI_PROCESSING else 'active'

        # Add initial processing_steps for queued state with ISO timestamp
        queued_step = {'queued': {'status': 'queued', 'ts': datetime.utcnow().isoformat()}}

        video = await db_client.create_video(
            user_id=current_user_id,
            title=title,
            cdn_url=cdn_url,
            filename=unique_filename,
            content_hash=content_hash,
            file_size=len(content),
            status=initial_status,
            processing_steps=queued_step
        )
        
        # Award tokens for upload
        video_id = str(video['id'])
        await db_client.earn_tokens(current_user_id, 10, "video_upload", video_id)

        # Trigger AI processing if enabled
        if settings.ENABLE_AI_PROCESSING:
            print(f"[UPLOAD] Triggering AI processing for video {video_id}")
            try:
                # Try to use Celery if available, otherwise log for manual processing
                process_video.delay(video_id)
                print(f"[UPLOAD] AI processing task queued for {video_id}")
                # Immediately mark processing as queued in DB so frontend shows
                # in-progress state even before worker picks it up. Use the
                # db_client to update processing_steps if available; we keep
                # this simple and defensive since db_client uses AsyncSurreal.
                try:
                    # Read the video record and do a safe read-modify-write of processing_steps
                    try:
                        existing = await db_client.get_video(video_id)
                    except Exception:
                        existing = None

                    processing = {}
                    if existing and isinstance(existing, dict):
                        processing = existing.get('processing_steps') or {}

                    # Set queued step with ISO timestamp (client will render this state)
                    processing['queued'] = {'status': 'queued', 'ts': datetime.utcnow().isoformat()}

                    # Parameterized update (avoid SurrealQL helpers which caused parse errors in some environments)
                    await db_client.db.query(
                        "UPDATE video SET processing_steps = $processing, status = 'processing' WHERE id = $id",
                        {"processing": processing, "id": video_id}
                    )
                except Exception as e:
                    print(f"[UPLOAD] Warning: Failed to update processing_steps in DB immediately: {e}")

                # Publish initial SSE event on Redis channel so clients see immediate update
                try:
                    import redis as redis_sync
                    r = redis_sync.from_url(settings.REDIS_URL)
                    channel = f"video:{video_id}:events"
                    payload = '{"type":"status","status":"processing","video_id":"%s"}' % (video_id)
                    r.publish(channel, payload)
                except Exception as e:
                    print(f"[UPLOAD] Warning: Failed to publish initial Redis event: {e}")
            except Exception as e:
                print(f"[UPLOAD] Warning: Celery not available ({e}), AI processing will need to be triggered manually")
                print(f"[UPLOAD] Video {video_id} ready for AI processing at {file_path}")

        return {
            "video_id": video_id,
            "playback_url": cdn_url,
            "title": title,
            "status": "success",
            "message": "Video uploaded successfully",
            "ai_processing_enabled": settings.ENABLE_AI_PROCESSING
        }
        
    except Exception as e:
        # Print full traceback to help debugging during local development
        print(f"Upload error: {repr(e)}")
        traceback.print_exc()
        # Return error type and message in detail for dev only
        err_detail = f"{e.__class__.__name__}: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Upload failed: {err_detail}")

