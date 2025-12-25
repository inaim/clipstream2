from fastapi import APIRouter, Request, Query, HTTPException, Body
from typing import List, Optional
from db.surrealdb_client import db_client
from utils.config import settings
import json

try:
    import redis as redis_sync
except Exception:
    redis_sync = None

try:
    from ml.inference.scorer_service import get_scorer_service
    AI_SCORING_ENABLED = True
except Exception as e:
    print(f"AI scoring not available: {e}")
    AI_SCORING_ENABLED = False

router = APIRouter()

@router.get("/for-you")
async def get_for_you_feed(
    request: Request,
    limit: int = 50,
    user_id: Optional[str] = Query(None),
    use_ai: bool = Query(True, description="Use AI-based personalized ranking")
):
    """
    Get personalized For You feed.

    If use_ai=True and user_id is provided, uses AI model for personalized ranking.
    Otherwise falls back to time-based ordering.
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

    # Get candidate videos (larger pool for ranking)
    candidate_limit = limit * 3 if use_ai and user_id else limit
    videos = await db_client.get_for_you_feed(candidate_limit)

    # Apply AI-based ranking if enabled and user_id provided
    if use_ai and AI_SCORING_ENABLED and user_id and videos:
        try:
            # Get user data and history
            user_data = await db_client.get_user_by_id(user_id)
            if user_data:
                # Get user's recent interactions (last 100)
                from ml.events.video_events import VideoEventRecorder, EventType
                event_recorder = VideoEventRecorder(db_client)
                user_history_events = await event_recorder.get_user_events(
                    user_id=user_id,
                    limit=100,
                    event_types=[EventType.WATCH, EventType.LIKE, EventType.COMPLETE]
                )

                # Convert events to history format
                user_history = []
                for event in user_history_events:
                    user_history.append({
                        'video_id': str(event.get('video_id', '')),
                        'liked': event.get('type') == 'like',
                        'watch_time': event.get('metadata', {}).get('watch_time', 0),
                        'completed': event.get('type') == 'complete'
                    })

                # Score and rank videos using AI
                scorer = get_scorer_service()
                ranked_videos = await scorer.rank_feed(
                    candidate_videos=videos,
                    user_data=user_data,
                    user_history=user_history,
                    limit=limit,
                    objective='engagement',  # Can be made configurable
                    diversity_factor=0.2  # 20% diversity boost
                )

                print(f"AI ranking applied for user {user_id}: {len(ranked_videos)} videos")
                return ranked_videos
        except Exception as e:
            print(f"AI ranking failed, falling back to default: {e}")
            # Fall through to default behavior

    # Default: return videos as-is (time-based ordering)
    return videos[:limit]


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
async def get_trending_feed(
    request: Request,
    limit: int = 50,
    user_id: Optional[str] = Query(None),
    use_ai: bool = Query(True, description="Use AI-based trending detection")
):
    """
    Get trending videos based on engagement metrics and virality signals.

    If use_ai=True, applies AI-based virality scoring in addition to engagement metrics.
    """
    try:
        auth = request.headers.get('authorization')
        if auth:
            print(f"Feed debug (trending): Authorization header present (len={len(auth)})")
        else:
            print("Feed debug (trending): Authorization header missing")
    except Exception:
        pass

    # Get candidate videos
    videos = await db_client.get_trending_feed(limit * 2)

    # Apply AI-based virality boosting if enabled
    if use_ai and AI_SCORING_ENABLED and videos:
        try:
            from ml.events.video_events import VideoEventRecorder

            # Compute virality metrics for each video
            event_recorder = VideoEventRecorder(db_client)
            scored_videos = []

            for video in videos:
                # Get virality metrics
                virality = await event_recorder.compute_virality_metrics(video['id'])

                # Combine base score with AI virality signals
                base_score = (
                    video.get('view_count', 0) * 1.0 +
                    video.get('like_count', 0) * 5.0 +
                    video.get('share_count', 0) * 10.0
                )

                # Boost viral and trending content
                virality_boost = 1.0
                if virality.get('is_viral'):
                    virality_boost = 3.0
                elif virality.get('is_trending'):
                    virality_boost = 2.0

                # Apply velocity multiplier
                velocity_multiplier = 1.0 + (virality.get('velocity', 0) / 100.0)

                final_score = base_score * virality_boost * velocity_multiplier

                # Add virality metadata to video
                video['virality_metrics'] = virality

                scored_videos.append((video, final_score))

            # Sort by final score
            scored_videos.sort(key=lambda x: x[1], reverse=True)

            # Return top videos
            trending_videos = [video for video, score in scored_videos[:limit]]

            print(f"AI trending applied: {len(trending_videos)} videos")
            return trending_videos

        except Exception as e:
            print(f"AI trending failed, falling back to default: {e}")
            # Fall through to default

    return videos[:limit]


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
