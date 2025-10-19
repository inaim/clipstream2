from celery import Celery
from utils.config import settings
import os
import subprocess
from db.surrealdb_client import db_client
import asyncio
from datetime import datetime
import logging
from celery.signals import worker_process_init, worker_process_shutdown

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
        # Diagnostic: log db_client state before connecting
        logger.info(f"[ENCODER] db_client exists: {db_client is not None}, _connected: {getattr(db_client, '_connected', False)}, db attr present: {hasattr(db_client, 'db') and getattr(db_client, 'db') is not None}")
        # Ensure the db_client is connected in this worker process
        try:
            if not getattr(db_client, '_connected', False):
                logger.info("[ENCODER] Attempting to connect db_client in worker process")
                asyncio.run(db_client.connect())
                logger.info(f"[ENCODER] After connect: _connected={getattr(db_client, '_connected', False)}, db attr present: {hasattr(db_client, 'db') and getattr(db_client, 'db') is not None}")
        except Exception as conn_exc:
            logger.error(f"[ENCODER] Failed to connect db_client in worker: {conn_exc}")

        # Fetch video record from DB to get file path
        logger.info(f"[ENCODER] Fetching video {video_id} from DB")
        video = asyncio.run(db_client.get_video(video_id))
        if not video:
            raise Exception(f"Video {video_id} not found in DB")
        input_path = os.path.join(settings.UPLOAD_DIR, video.get('filename', ''))
        if not os.path.exists(input_path):
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
        gcs_url = upload_to_gcs(output_360p, video_id, '360p-av1.mkv')
        logger.info(f"[ENCODER] Uploaded 360p AV1 to GCS: {gcs_url}")

        # Update SurrealDB record with CDN URL and mark status active
        def update_db():
            # Merge into cdn_urls object and set primary cdn_url if not set
            return db_client.db.query(
                "UPDATE video SET cdn_urls = merge(cdn_urls, { '360p_av1': $url }), cdn_url = $url, status = 'active' WHERE id = $id",
                {"url": gcs_url, "id": video_id}
            )
        asyncio.run(update_db())

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
        logger.info("[CELERY SIGNAL] worker_process_init: connecting db_client")
        asyncio.run(db_client.connect())
        logger.info("[CELERY SIGNAL] db_client connected in worker process")
    except Exception as e:
        logger.error(f"[CELERY SIGNAL] Failed to connect db_client in worker process: {e}")


@worker_process_shutdown.connect
def celery_worker_shutdown(**kwargs):
    """Disconnect the SurrealDB client when a worker process exits."""
    try:
        logger.info("[CELERY SIGNAL] worker_process_shutdown: disconnecting db_client")
        asyncio.run(db_client.disconnect())
        logger.info("[CELERY SIGNAL] db_client disconnected in worker process")
    except Exception as e:
        logger.warning(f"[CELERY SIGNAL] Error disconnecting db_client: {e}")
