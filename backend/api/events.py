"""
Event Logging API

Handles user interaction events and updates video/user statistics in real-time.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import time
import logging

from db.surrealdb_client import db_client
from app.event_logger import log_event, batch_log_events, get_video_analytics, get_user_analytics

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class EventCreate(BaseModel):
    """User interaction event."""
    user_id: str = Field(..., description="User ID (e.g., 'user:123')")
    video_id: str = Field(..., description="Video ID (e.g., 'video:456')")
    event_type: str = Field(..., description="Event type: play_end, skip, like, unlike, rewatch, share, comment")
    watch_ratio: Optional[float] = Field(0.0, description="Percentage of video watched (0.0-1.0)")
    category: Optional[str] = Field(None, description="Video category")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional event metadata")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user:123",
                "video_id": "video:456",
                "event_type": "play_end",
                "watch_ratio": 0.85,
                "category": "sports",
                "metadata": {"device": "mobile", "session_id": "abc123"}
            }
        }


class EventBatchCreate(BaseModel):
    """Batch of events to log."""
    events: List[EventCreate] = Field(..., description="List of events to log")


class EventResponse(BaseModel):
    """Event logging response."""
    success: bool
    message: str
    timestamp: float


# ============================================
# EVENT ENDPOINTS
# ============================================

@router.post("/events", response_model=EventResponse, tags=["Events"])
async def create_event(event: EventCreate):
    """
    Log a user interaction event.

    This endpoint:
    - Records the event in the database
    - Updates video statistics (impressions, watch ratio, etc.)
    - Updates user interest profile (category preferences)
    - Powers the ML recommendation algorithm

    **Event Types:**
    - `play_end` - Video finished/stopped
    - `skip` - Video skipped early
    - `like` - Video liked
    - `unlike` - Video unliked
    - `rewatch` - Video rewatched
    - `share` - Video shared
    - `comment` - Comment added

    **Watch Ratio:**
    - 0.0 = Not watched
    - 0.5 = Watched 50%
    - 1.0 = Watched completely
    """
    try:
        # Get async DB client
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Prepare event data
        event_data = {
            "user_id": event.user_id,
            "video_id": event.video_id,
            "event_type": event.event_type,
            "watch_ratio": event.watch_ratio or 0.0,
            "category": event.category or "unknown",
            "timestamp": time.time(),
            "metadata": event.metadata or {},
        }

        # Log the event
        success = await log_event(async_db, event_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to log event")

        return EventResponse(
            success=True,
            message=f"Event '{event.event_type}' logged successfully",
            timestamp=event_data["timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")


@router.post("/events/batch", response_model=dict, tags=["Events"])
async def create_events_batch(batch: EventBatchCreate):
    """
    Log multiple events in a single request.

    Useful for:
    - Offline event batching
    - Reducing API calls
    - Bulk import of historical data

    Returns counts of successful/failed events.
    """
    try:
        # Get async DB client
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Prepare event data list
        events_data = []
        current_time = time.time()

        for event in batch.events:
            event_data = {
                "user_id": event.user_id,
                "video_id": event.video_id,
                "event_type": event.event_type,
                "watch_ratio": event.watch_ratio or 0.0,
                "category": event.category or "unknown",
                "timestamp": current_time,
                "metadata": event.metadata or {},
            }
            events_data.append(event_data)

        # Batch log
        result = await batch_log_events(async_db, events_data)

        return {
            "success": True,
            "total": result["total"],
            "successful": result["success"],
            "failed": result["failed"],
            "errors": result["errors"],
        }

    except Exception as e:
        logger.error(f"Failed to create event batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log events: {str(e)}")


# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@router.get("/events/analytics/video/{video_id}", response_model=dict, tags=["Analytics"])
async def get_video_event_analytics(video_id: str):
    """
    Get detailed analytics for a video.

    Returns:
    - Total impressions
    - Average watch ratio
    - Completion rate
    - Like rate
    - Skip rate
    - Rewatch rate
    - Raw statistics
    """
    try:
        # Get async DB client
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")

        analytics = await get_video_analytics(async_db, video_id)

        if not analytics:
            raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found")

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/events/analytics/user/{user_id}", response_model=dict, tags=["Analytics"])
async def get_user_event_analytics(user_id: str):
    """
    Get detailed analytics for a user.

    Returns:
    - Total events logged
    - Category preferences (impressions, watch ratio, like rate per category)
    - Unique videos watched
    """
    try:
        # Get async DB client
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")

        analytics = await get_user_analytics(async_db, user_id)

        if not analytics:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
