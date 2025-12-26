from fastapi import APIRouter, Request, Query, HTTPException, Body
from typing import List, Optional
from db.surrealdb_client import db_client
from utils.config import settings
from app.scoring import rank_videos_for_user, explain_score
import json
import time

try:
    import redis as redis_sync
except Exception:
    redis_sync = None

router = APIRouter()

@router.get("/for-you")
async def get_for_you_feed(
    request: Request,
    user_id: Optional[str] = Query(None, description="User ID for personalized ranking"),
    limit: int = Query(50, description="Number of videos to return"),
    use_ml: bool = Query(True, description="Use ML ranking algorithm")
):
    """
    Get personalized "For You" feed using TikTok-style ML ranking.

    **Without user_id:** Returns all active videos (no personalization)
    **With user_id:** Returns ML-ranked videos based on:
    - User interest (60%): Category preferences + embedding similarity
    - Video quality (30%): Engagement metrics + age decay
    - Exploration (10%): Discovery bonus for unseen videos

    **Parameters:**
    - user_id: Optional user ID for personalized ranking
    - limit: Number of videos to return (default: 50)
    - use_ml: Enable ML ranking (default: true)
    """
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

    # Get candidate videos
    candidate_videos = await db_client.get_for_you_feed(limit * 3)  # Get 3x for better ranking

    # Drop any videos pointing to the deprecated finailabz CDN to avoid TLS errors in dev
    if candidate_videos:
        filtered = []
        for v in candidate_videos:
            cdn = str(v.get("cdn_url") or "")
            if "cdn.finailabz.com" in cdn:
                continue
            filtered.append(v)
        candidate_videos = filtered

    # If no user_id or ML disabled, return unranked
    if not user_id or not use_ml or not candidate_videos:
        return candidate_videos[:limit] if candidate_videos else []

    try:
        # Get async DB client
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            print("Warning: async_db not available, returning unranked feed")
            return candidate_videos[:limit]

        # Fetch user data
        user_result = await async_db.query(f"SELECT * FROM {user_id}")
        if not user_result or len(user_result) == 0 or not user_result[0].get("result"):
            # User not found, return unranked
            return candidate_videos[:limit]

        user = user_result[0]["result"][0]

        # Rank videos using ML algorithm
        ranked_videos = rank_videos_for_user(
            user=user,
            candidate_videos=candidate_videos,
            limit=limit,
            now=time.time()
        )

        return ranked_videos

    except Exception as e:
        print(f"ML ranking failed: {e}, falling back to unranked feed")
        return candidate_videos[:limit]


@router.get("/debug/recent-videos")
async def debug_recent_videos(limit: int = 10):
    """Development-only helper: return recent videos (for debugging uploads visible in DB)."""
    videos = await db_client.get_for_you_feed(limit)
    # Only available in non-production
    return {
        "env": getattr(db_client, 'ENVIRONMENT', 'unknown'),
        "count": len(videos or []),
        "videos": videos or []
    }


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


@router.post('/debug/seed-video')
async def seed_demo_video(payload: dict = Body(default=None)):
    """Create a development-only demo video record and publish SSE/Redis events so clients see it immediately.

    Accepts JSON body: {"title": "...", "user_id": "user:...", "force": true}
    """
    title = "Demo Video"
    user_id = None
    force = False
    if payload:
        title = payload.get('title', title)
        user_id = payload.get('user_id')
        force = bool(payload.get('force', False))
    """Create a development-only demo video record and publish SSE/Redis events so clients see it immediately.

    This endpoint is intentionally disabled in production unless `force=true` is provided.
    """
    # Protect against accidental production use
    if settings.is_production() and not force:
        raise HTTPException(status_code=403, detail="Seed endpoint disabled in production")

    # Default demo user if none provided
    # Use a public small demo MP4 so clients can play it if needed
    demo_cdn = 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4'

    # If no user_id provided, create a demo user and use it as the creator
    user = user_id
    creator_profile = None
    try:
        if not user:
            # Create a demo user via db_client.create_user
            # create_user requires email and password_hash; use a predictable demo email
            from datetime import datetime
            now = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            demo_email = f"demo+{now}@example.com"
            created = await db_client.create_user(demo_email, password_hash='', display_name='Demo User')
            # created may be a dict with id or similar
            if isinstance(created, dict):
                user = created.get('id') or created.get('_id') or None
                # Build a profiles-like object for frontend convenience
                creator_profile = {
                    'display_name': created.get('display_name') or 'Demo User',
                    'username': getattr(created, 'username', created.get('email', 'demo')),
                    'avatar_url': created.get('avatar_url') if isinstance(created.get('avatar_url'), str) else ''
                }
        else:
            # Try to fetch existing user profile fields for inclusion in the payload
            try:
                fetched = await db_client.get_user_by_id(user)
                if fetched and isinstance(fetched, dict):
                    creator_profile = {
                        'display_name': fetched.get('display_name') or fetched.get('email', 'Creator'),
                        'username': fetched.get('username') or (fetched.get('email') or 'creator').split('@')[0],
                        'avatar_url': fetched.get('avatar_url') or ''
                    }
            except Exception:
                creator_profile = None
    except Exception:
        # Non-fatal; fall back to anonymous demo creator
        user = user or 'user:demo'
        creator_profile = creator_profile or {'display_name': 'Demo User', 'username': 'demo', 'avatar_url': ''}

    try:
        video = await db_client.create_video(
            user_id=user,
            title=title,
            cdn_url=demo_cdn,
            filename='demo.mp4',
            content_hash='demo',
            file_size=0,
            status='active'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demo video: {e}")

    # Normalize id to string for consumption by clients
    try:
        if isinstance(video, dict):
            vid = video.get('id') or video.get('_id') or video.get('ID') or None
        else:
            vid = video
        vid = str(vid)
    except Exception:
        vid = None

    # Publish Redis events (best-effort)
    try:
        if redis_sync is not None:
            r = redis_sync.from_url(settings.REDIS_URL)
            channel = f"video:{vid}:events"
            payload = json.dumps({"type": "status", "status": "active", "video_id": vid})
            try:
                r.publish(channel, payload)
            except Exception:
                pass

            try:
                global_channel = "videos:events"
                # Ensure we include a profiles-like object and initial counts so frontend
                # can render the VideoCard immediately without extra fetches.
                profiles_payload = creator_profile or {'display_name': 'Demo User', 'username': 'demo', 'avatar_url': ''}
                global_payload = json.dumps({
                    "type": "video_created",
                    "video": {
                        "id": vid,
                        "title": title,
                        "cdn_url": demo_cdn,
                        "status": "active",
                        "likes_count": 0,
                        "comments_count": 0,
                        "shares_count": 0,
                        "profiles": profiles_payload
                    }
                })
                r.publish(global_channel, global_payload)
            except Exception:
                pass
    except Exception:
        # non-fatal
        pass

    return {"video": video}


@router.get("/debug/explain-score")
async def explain_video_score(
    user_id: str = Query(..., description="User ID"),
    video_id: str = Query(..., description="Video ID")
):
    """
    Debug endpoint: Explain the ML ranking score for a (user, video) pair.

    Returns detailed breakdown of:
    - Total score
    - Video quality component
    - User interest component
    - Exploration component
    - Raw video stats
    - User category stats
    """
    try:
        # Get async DB client
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Fetch user
        user_result = await async_db.query(f"SELECT * FROM {user_id}")
        if not user_result or len(user_result) == 0 or not user_result[0].get("result"):
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
        user = user_result[0]["result"][0]

        # Fetch video
        video_result = await async_db.query(f"SELECT * FROM {video_id}")
        if not video_result or len(video_result) == 0 or not video_result[0].get("result"):
            raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found")
        video = video_result[0]["result"][0]

        # Explain score
        explanation = explain_score(user, video, now=time.time())

        return explanation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain score: {str(e)}")
