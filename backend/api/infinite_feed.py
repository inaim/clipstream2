"""
Infinite Feed API - TikTok-style Infinite Scroll

Efficient cursor-based pagination with real-time ML optimization.
Designed for high-volume event tracking and instant personalization.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from db.surrealdb_client import db_client
from app.scoring import rank_videos_for_user
from app.event_logger import log_event

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MODELS
# ============================================================================

class InfiniteFeedRequest(BaseModel):
    """Request for infinite feed."""
    user_id: str
    cursor: Optional[str] = None  # Last video ID seen
    limit: int = Field(default=10, ge=1, le=50)
    exclude_seen: bool = True  # Filter out videos user has already seen


class InfiniteFeedResponse(BaseModel):
    """Response for infinite feed."""
    videos: List[Dict[str, Any]]
    next_cursor: Optional[str] = None
    has_more: bool = True
    total_candidates: int = 0
    personalization_score: float = 0.0


class FeedEventBatch(BaseModel):
    """Batch of feed events for efficient logging."""
    user_id: str
    events: List[Dict[str, Any]]  # List of {video_id, event_type, watch_ratio, timestamp}


# ============================================================================
# INFINITE SCROLL FEED - Cursor-based Pagination
# ============================================================================

@router.post("/infinite", response_model=InfiniteFeedResponse)
async def get_infinite_feed(request: InfiniteFeedRequest):
    """
    Get infinite scroll feed with cursor-based pagination.

    TikTok-style architecture:
    - Cursor-based pagination (not offset-based)
    - Excludes already-seen videos
    - Real-time ML personalization
    - Efficient video fetching

    Args:
        request: Feed request with user_id, cursor, limit

    Returns:
        Personalized video feed with next cursor
    """
    try:
        start_time = time.time()
        async_db = getattr(db_client, "async_db", None)

        if not async_db:
            raise HTTPException(status_code=500, detail="Database not connected")

        # Get user profile
        user_result = await async_db.query(f"SELECT * FROM {request.user_id}")
        if not user_result or not user_result[0]["result"]:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result[0]["result"][0]

        # Get user's seen video IDs (for filtering)
        seen_video_ids = set()
        if request.exclude_seen:
            events_query = f"""
                SELECT video_id FROM event
                WHERE user_id = '{request.user_id}'
                AND event_type IN ['play_end', 'skip', 'like']
            """
            events_result = await async_db.query(events_query)
            if events_result and events_result[0]["result"]:
                seen_video_ids = {evt["video_id"] for evt in events_result[0]["result"]}

        # Fetch candidate videos (more than requested for better ranking)
        fetch_limit = request.limit * 5  # Fetch 5x for ranking pool

        # Build cursor query
        if request.cursor:
            # Cursor = last video ID
            cursor_condition = f"AND id > '{request.cursor}'"
        else:
            cursor_condition = ""

        # Fetch videos
        videos_query = f"""
            SELECT * FROM video
            WHERE status = 'active'
            {cursor_condition}
            ORDER BY id ASC
            LIMIT {fetch_limit}
        """

        videos_result = await async_db.query(videos_query)

        if not videos_result or not videos_result[0]["result"]:
            return InfiniteFeedResponse(
                videos=[],
                next_cursor=None,
                has_more=False,
                total_candidates=0,
                personalization_score=0.0
            )

        candidate_videos = videos_result[0]["result"]

        # Filter out seen videos
        if request.exclude_seen:
            candidate_videos = [
                v for v in candidate_videos
                if v["id"] not in seen_video_ids
            ]

        if not candidate_videos:
            return InfiniteFeedResponse(
                videos=[],
                next_cursor=None,
                has_more=False,
                total_candidates=0,
                personalization_score=0.0
            )

        # Rank videos using ML algorithm
        now = time.time()
        ranked_videos = rank_videos_for_user(
            user=user,
            candidate_videos=candidate_videos,
            limit=request.limit,
            now=now
        )

        # Calculate personalization score (average of top videos)
        personalization_score = 0.0
        if ranked_videos:
            personalization_score = sum(v.get("score", 0) for v in ranked_videos) / len(ranked_videos)

        # Get next cursor (last video ID in result)
        next_cursor = None
        has_more = False

        if ranked_videos:
            next_cursor = ranked_videos[-1]["id"]
            # Check if there are more videos after this cursor
            has_more = len(candidate_videos) >= fetch_limit

        elapsed_time = time.time() - start_time
        logger.info(
            f"Infinite feed generated for {request.user_id}: "
            f"{len(ranked_videos)} videos, {elapsed_time:.3f}s, "
            f"personalization={personalization_score:.3f}"
        )

        return InfiniteFeedResponse(
            videos=ranked_videos,
            next_cursor=next_cursor,
            has_more=has_more,
            total_candidates=len(candidate_videos),
            personalization_score=personalization_score
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating infinite feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH EVENT LOGGING - High-volume event tracking
# ============================================================================

@router.post("/events/batch")
async def log_events_batch(batch: FeedEventBatch):
    """
    Log multiple events in a single batch for efficiency.

    TikTok-style event tracking:
    - Batch processing for high volume
    - Async event logging
    - Real-time stats updates

    Args:
        batch: Batch of events from frontend

    Returns:
        Success status and logged count
    """
    try:
        async_db = getattr(db_client, "async_db", None)

        if not async_db:
            raise HTTPException(status_code=500, detail="Database not connected")

        logged_count = 0

        for event_data in batch.events:
            # Build full event
            full_event = {
                "user_id": batch.user_id,
                "video_id": event_data["video_id"],
                "event_type": event_data["event_type"],
                "watch_ratio": event_data.get("watch_ratio", 0.0),
                "category": event_data.get("category", "general"),
                "timestamp": event_data.get("timestamp", time.time())
            }

            # Log event (updates stats in real-time)
            success = await log_event(async_db, full_event)

            if success:
                logged_count += 1

        logger.info(f"Batch logged {logged_count}/{len(batch.events)} events for {batch.user_id}")

        return {
            "success": True,
            "logged_count": logged_count,
            "total_events": len(batch.events)
        }

    except Exception as e:
        logger.error(f"Error logging event batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREFETCH - Get next batch while user is watching
# ============================================================================

@router.get("/prefetch")
async def prefetch_next_videos(
    user_id: str = Query(...),
    cursor: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Prefetch next batch of videos while user is watching current batch.

    TikTok optimization:
    - Fetch next videos in background
    - Reduce perceived loading time
    - Improve UX with instant scrolling

    Args:
        user_id: User ID
        cursor: Last video ID from previous batch
        limit: Number of videos to prefetch

    Returns:
        Next batch of videos
    """
    request = InfiniteFeedRequest(
        user_id=user_id,
        cursor=cursor,
        limit=limit,
        exclude_seen=True
    )

    return await get_infinite_feed(request)


# ============================================================================
# REFRESH FEED - Get updated feed based on new interactions
# ============================================================================

@router.post("/refresh")
async def refresh_feed(user_id: str = Query(...), limit: int = Query(10)):
    """
    Refresh feed with latest ML recommendations.

    Use case:
    - User pulls down to refresh
    - Get newly personalized content
    - Incorporate latest interactions

    Args:
        user_id: User ID
        limit: Number of videos

    Returns:
        Refreshed personalized feed
    """
    request = InfiniteFeedRequest(
        user_id=user_id,
        cursor=None,  # Start from beginning
        limit=limit,
        exclude_seen=True  # Don't show already-seen videos
    )

    return await get_infinite_feed(request)


# ============================================================================
# ANALYTICS - Feed performance metrics
# ============================================================================

@router.get("/analytics/feed-quality")
async def get_feed_quality_metrics(user_id: str = Query(...)):
    """
    Get feed quality metrics for a user.

    Metrics:
    - Average watch ratio
    - Skip rate
    - Like rate
    - Engagement score

    Args:
        user_id: User ID

    Returns:
        Feed quality metrics
    """
    try:
        async_db = getattr(db_client, "async_db", None)

        if not async_db:
            raise HTTPException(status_code=500, detail="Database not connected")

        # Get user's recent events (last 50)
        events_query = f"""
            SELECT * FROM event
            WHERE user_id = '{user_id}'
            ORDER BY timestamp DESC
            LIMIT 50
        """

        events_result = await async_db.query(events_query)

        if not events_result or not events_result[0]["result"]:
            return {
                "user_id": user_id,
                "total_events": 0,
                "avg_watch_ratio": 0.0,
                "skip_rate": 0.0,
                "like_rate": 0.0,
                "engagement_score": 0.0
            }

        events = events_result[0]["result"]

        # Calculate metrics
        total_events = len(events)
        watch_ratios = [e.get("watch_ratio", 0) for e in events]
        skips = sum(1 for e in events if e["event_type"] == "skip")
        likes = sum(1 for e in events if e["event_type"] == "like")

        avg_watch_ratio = sum(watch_ratios) / len(watch_ratios) if watch_ratios else 0.0
        skip_rate = skips / total_events if total_events > 0 else 0.0
        like_rate = likes / total_events if total_events > 0 else 0.0

        # Engagement score (0-1): higher is better
        # Formula: avg_watch_ratio * (1 - skip_rate) * (1 + like_rate)
        engagement_score = avg_watch_ratio * (1 - skip_rate) * (1 + like_rate)

        return {
            "user_id": user_id,
            "total_events": total_events,
            "avg_watch_ratio": round(avg_watch_ratio, 3),
            "skip_rate": round(skip_rate, 3),
            "like_rate": round(like_rate, 3),
            "engagement_score": round(engagement_score, 3)
        }

    except Exception as e:
        logger.error(f"Error calculating feed quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))
