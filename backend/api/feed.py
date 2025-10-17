from fastapi import APIRouter, Request, Query
from typing import List
from db.surrealdb_client import db_client

router = APIRouter()

@router.get("/for-you")
async def get_for_you_feed(request: Request, limit: int = 50):
    # Masked debug: indicate whether Authorization header is present (do not log token value)
    try:
        auth = request.headers.get('authorization')
        if auth:
            # Only log length to avoid leaking token
            print(f"Feed debug: Authorization header present (len={len(auth)})")
        else:
            print("Feed debug: Authorization header missing")
    except Exception:
        pass

    videos = await db_client.get_for_you_feed(limit)
    return videos


@router.get("/following")
async def get_following_feed(request: Request, user_id: str = Query(...), limit: int = 50):
    """Get videos from users that the current user follows"""
    try:
        auth = request.headers.get('authorization')
        if auth:
            print(f"Feed debug (following): Authorization header present (len={len(auth)})")
        else:
            print("Feed debug (following): Authorization header missing")
    except Exception:
        pass

    videos = await db_client.get_following_feed(user_id, limit)
    return videos


@router.get("/trending")
async def get_trending_feed(request: Request, limit: int = 50):
    """Get trending videos based on engagement metrics"""
    try:
        auth = request.headers.get('authorization')
        if auth:
            print(f"Feed debug (trending): Authorization header present (len={len(auth)})")
        else:
            print("Feed debug (trending): Authorization header missing")
    except Exception:
        pass

    videos = await db_client.get_trending_feed(limit)
    return videos
