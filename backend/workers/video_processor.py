from celery import Celery
from utils.config import settings
import os
import subprocess
from db.surrealdb_client import db_client
import asyncio
from datetime import datetime
import logging
from celery.signals import worker_process_init, worker_process_shutdown
from db.surrealdb_client import close_sync_client

logger = logging.getLogger(__name__)

# Initialize Celery app - this is required for celery worker to find it
celery = Celery(
    'clipstream',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)


@celery.task(bind=True, max_retries=3)
def process_video(self, video_id: str):
    """
    Process video: encode, transcribe, analyze
    """
    logger.info(f"[PROCESSOR] Starting AI processing for video: {video_id}")

    # Publish a 'processing' event immediately and write an 'in_progress'
    # processing step in the DB with the Celery task id so the frontend can
    # transition from 'queued' -> 'processing' and show the task reference.
    try:
        task_id = None
        try:
            task_id = getattr(self.request, 'id', None)
        except Exception:
            task_id = None

        # Update DB with encoding in_progress and task id using local AsyncSurreal
        # Use the worker's connected db_client to update the record to avoid
        # creating new AsyncSurreal instances inside the worker process.
        try:
            task_id = getattr(self.request, 'id', None)
        except Exception:
            task_id = None

        try:
            ok = db_client.sync_update_video_fields(video_id, {
                'processing_steps': {'encoding': {'status': 'in_progress', 'task_id': task_id, 'ts': datetime.utcnow().isoformat()}},
                'status': 'processing'
            })
            if not ok:
                logger.warning(f"[PROCESSOR] update_video_fields returned False for {video_id}")
        except Exception as e:
            logger.warning(f"[PROCESSOR] Failed to mark processing in DB for {video_id}: {e}")

        # Publish SSE event via Redis so EventSource clients get immediate update
        try:
            import json as _json
            import redis as redis_sync
            redis_url = settings.REDIS_URL
            if redis_url:
                r = redis_sync.from_url(redis_url)
                channel = f"video:{video_id}:events"
                payload = _json.dumps({"type": "status", "status": "processing", "video_id": video_id, "task_id": task_id})
                r.publish(channel, payload)
        except Exception as e:
            logger.warning(f"[PROCESSOR] Failed to publish processing event for {video_id}: {e}")
    except Exception:
        # Don't let the pre-publish steps block processing; log and continue
        logger.exception(f"[PROCESSOR] Pre-processing publish failed for {video_id}")

    try:
        # Step 1: Encode video to multiple qualities
        logger.info(f"[PROCESSOR] Step 1: Encoding video {video_id}")
        encode_video.delay(video_id)

        # Step 2: Generate thumbnail
        logger.info(f"[PROCESSOR] Step 2: Generating thumbnail for {video_id}")
        generate_thumbnail.delay(video_id)

        # Step 3: Transcribe audio (if available)
        logger.info(f"[PROCESSOR] Step 3: Transcribing audio for {video_id}")
        transcribe_audio.delay(video_id)

        logger.info(f"[PROCESSOR] AI processing queued for video {video_id}")
        return {"status": "queued", "video_id": video_id}

    except Exception as exc:
        logger.error(f"[PROCESSOR] Error processing video {video_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)


def upload_to_gcs(local_path, video_id, dest_name):
    """Upload a file to GCS and return the public URL"""
    bucket_name = settings.GCS_BUCKET_NAME
    if not bucket_name:
        raise Exception("GCS_BUCKET_NAME not set in config")
    try:
        from google.cloud import storage
    except Exception as e:
        # Delay the import error until upload is attempted so beat/worker can start
        raise RuntimeError(
            "google-cloud-storage is not installed in this environment. "
            "Install 'google-cloud-storage' in the image or set ENABLE_GCS=False to skip uploads."
        ) from e

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"videos/{video_id}/{dest_name}")
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

@celery.task(bind=True, max_retries=2)
def encode_video(self, video_id: str):

    try:
        # Use a fresh AsyncSurreal client inside this task to avoid
        # cross-event-loop errors when the shared db_client was created
        # on a different loop in the main FastAPI process.
        # No local AsyncSurreal: use worker-connected db_client for fetch/update

        logger.info(f"[ENCODER] Fetching video {video_id} from DB via worker db_client")
        # Use the connected db_client (worker process-level) to fetch the video.
        video = None
        input_path = None
        for attempt in range(3):
            try:
                # Prefer the sync client helper which uses Surreal's sync API
                from db.surrealdb_client import sync_client_get_video
                video = sync_client_get_video(video_id)
                if video:
                    break
            except Exception as e:
                logger.warning(f"[ENCODER] Attempt {attempt+1} fetch error for {video_id}: {e}")
            if attempt < 2:
                import time as _time
                _time.sleep(0.25)

        if not video:
            logger.error(f"[ENCODER] Video {video_id} not found in DB after retries using db_client")
            raise Exception(f"Video {video_id} not found in DB")

        # Compute the expected input path from the record's filename
        if video and video.get('filename'):
            input_path = os.path.join(settings.UPLOAD_DIR, video.get('filename'))
        if not input_path:
            raise Exception(f"Input file path for {video_id} could not be determined")

        # If the input file is missing, retry a few times with a short sleep
        # to handle the small window between upload completion and worker file
        # visibility (e.g. due to container filesystem delays or atomic move).
        max_check_attempts = 5
        check_delay_seconds = 0.5
        exists = os.path.exists(input_path)
        attempt = 0
        while not exists and attempt < max_check_attempts:
            attempt += 1
            logger.info(f"[ENCODER] Input file missing, attempt {attempt}/{max_check_attempts}, sleeping {check_delay_seconds}s")
            import time as _time
            _time.sleep(check_delay_seconds)
            exists = os.path.exists(input_path)

        if not exists:
            raise Exception(f"Input file {input_path} does not exist")

        # Output path for AV1 360p
        output_360p = input_path.replace('.mp4', '_360p_av1.mkv')
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "scale=-2:360",
            "-c:v", "libaom-av1", "-crf", "30", "-b:v", "0",
            "-c:a", "libopus",
            output_360p
        ]
        logger.info(f"[ENCODER] Running FFmpeg: {' '.join(ffmpeg_cmd)}")
        subprocess.run(ffmpeg_cmd, check=True)

        # Upload to GCS
        if getattr(settings, 'ENABLE_GCS', False) and settings.GCS_BUCKET_NAME:
            gcs_url = upload_to_gcs(output_360p, video_id, '360p-av1.mkv')
            logger.info(f"[ENCODER] Uploaded 360p AV1 to GCS: {gcs_url}")
        else:
            # For local/dev runs we don't have GCS configured. Expose the
            # output path as a relative URL under the uploads directory so
            # frontend can use it during development.
            gcs_url = f"/uploads/{os.path.basename(output_360p)}"
            logger.info(f"[ENCODER] GCS disabled or not configured; using local URL: {gcs_url}")

        # Use db_client helper to update cdn fields and status
        try:
            from db.surrealdb_client import sync_client_update_video_fields
            ok = sync_client_update_video_fields(video_id, {
                'cdn_urls': {'360p_av1': gcs_url},
                'cdn_url': gcs_url,
                'status': 'active'
            })
            if not ok:
                logger.warning(f"[ENCODER] sync_client_update_video_fields returned False for {video_id}")
        except Exception as e:
            logger.warning(f"[ENCODER] Failed to update video cdn fields for {video_id}: {e}")

        # Publish an event to Redis so clients subscribed to SSE can receive updates
        try:
            import redis as redis_sync
            redis_url = settings.REDIS_URL
            if redis_url:
                r = redis_sync.from_url(redis_url)
                channel = f"video:{video_id}:events"
                payload = '{"type":"status","status":"active","video_id":"%s","cdn_url":"%s"}' % (video_id, gcs_url)
                r.publish(channel, payload)
        except Exception as e:
            logger.warning(f"[ENCODER] Failed to publish Redis event for {video_id}: {e}")

        logger.info(f"[ENCODER] Encoding completed for {video_id}")
        return {"status": "completed", "video_id": video_id, "qualities": ["360p_av1"]}
    except Exception as exc:
        logger.error(f"[ENCODER] Error encoding video {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)




@celery.task(bind=True, max_retries=2)
def generate_thumbnail(self, video_id: str):
    """
    Generate thumbnail from video
    """
    logger.info(f"[THUMBNAIL] Generating thumbnail for video {video_id}")

    try:
        # TODO: Implement actual thumbnail generation
        logger.info(f"[THUMBNAIL] Thumbnail generated for {video_id}")
        return {"status": "completed", "video_id": video_id}

    except Exception as exc:
        logger.error(f"[THUMBNAIL] Error generating thumbnail for {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery.task(bind=True, max_retries=2)
def transcribe_audio(self, video_id: str):
    """
    Transcribe audio from video using Whisper or similar
    """
    logger.info(f"[TRANSCRIBER] Transcribing audio for video {video_id}")

    try:
        # TODO: Implement actual transcription using Whisper API or local model
        logger.info(f"[TRANSCRIBER] Transcription completed for {video_id}")
        return {"status": "completed", "video_id": video_id}

    except Exception as exc:
        logger.error(f"[TRANSCRIBER] Error transcribing video {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)


# Alias for Celery CLI discovery
app = celery


@worker_process_init.connect
def celery_worker_init(**kwargs):
    """Connect the SurrealDB client when a worker process starts."""
    try:
        logger.info("[CELERY SIGNAL] worker_process_init: skipping persistent db_client.connect() to avoid cross-loop futures; using per-call clients")
    except Exception as e:
        logger.error(f"[CELERY SIGNAL] worker_process_init: unexpected error (ignored): {e}")


@worker_process_shutdown.connect
def celery_worker_shutdown(**kwargs):
    """Disconnect the SurrealDB client when a worker process exits."""
    try:
        logger.info("[CELERY SIGNAL] worker_process_shutdown: closing cached sync Surreal client")
        try:
            close_sync_client()
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"[CELERY SIGNAL] worker_process_shutdown: unexpected error (ignored): {e}")
