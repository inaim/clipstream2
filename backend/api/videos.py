from fastapi import APIRouter, HTTPException
from typing import List
from db.surrealdb_client import db_client

router = APIRouter()


@router.get('/videos')
async def list_videos(limit: int = 50, offset: int = 0):
    """List videos (compatibility endpoint used by frontend). Returns a JSON array."""
    videos = await db_client.get_for_you_feed(limit)
    # db_client.get_for_you_feed returns a list; ensure we return an array
    return videos or []


@router.get('/videos/{video_id}')
async def get_video(video_id: str):
    video = await db_client.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail='Not Found')
    return video
