from fastapi import APIRouter
from typing import List
from db.surrealdb_client import db_client

router = APIRouter()

@router.get("/for-you")
async def get_for_you_feed(limit: int = 50):
    videos = await db_client.get_for_you_feed(limit)
    return videos
