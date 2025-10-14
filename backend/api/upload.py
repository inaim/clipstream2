from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import os
import uuid
import hashlib
from datetime import datetime
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

# Upload directory
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/app/uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        
        # Create video record in database
        video = await db_client.create_video(
            user_id=current_user_id,
            title=title,
            cdn_url=cdn_url,
            filename=unique_filename,
            content_hash=content_hash,
            file_size=len(content),
            status='active'
        )
        
        # Award tokens for upload
        video_id = str(video['id'])
        await db_client.earn_tokens(current_user_id, 10, "video_upload", video_id)
        
        return {
            "video_id": video_id,
            "playback_url": cdn_url,
            "title": title,
            "status": "success",
            "message": "Video uploaded successfully"
        }
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

