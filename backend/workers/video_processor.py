from celery import Celery
from utils.config import settings

celery_app = Celery(
    'clipstream',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task
def process_video(video_id: str):
    print(f"Processing video: {video_id}")
    return {"status": "completed", "video_id": video_id}
