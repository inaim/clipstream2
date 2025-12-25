"""
Real-time Event Streaming - Server-Sent Events (SSE)

Provides real-time updates to frontend when ML algorithm learns from user interactions.
TikTok-style instant feedback loop.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as aioredis

from utils.config import settings
from db.surrealdb_client import db_client
from app.event_logger import log_event

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# REDIS PUB/SUB - For real-time event broadcasting
# ============================================================================

redis_client: Optional[aioredis.Redis] = None


async def get_redis():
    """Get Redis client for pub/sub."""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def publish_event(channel: str, event_data: Dict[str, Any]):
    """
    Publish event to Redis channel.

    Args:
        channel: Redis channel name
        event_data: Event data to publish
    """
    try:
        redis = await get_redis()
        await redis.publish(channel, json.dumps(event_data))
    except Exception as e:
        logger.error(f"Failed to publish event to Redis: {e}")


# ============================================================================
# EVENT MODELS
# ============================================================================

class RealtimeEvent(BaseModel):
    """Real-time event from frontend."""
    user_id: str
    video_id: str
    event_type: str  # 'swipe_up', 'swipe_down', 'like', 'skip', 'play_end'
    watch_ratio: float
    category: str
    timestamp: Optional[float] = None


class MLFeedback(BaseModel):
    """ML algorithm feedback to frontend."""
    user_id: str
    event_type: str
    video_id: str
    category: str
    updated_preferences: Dict[str, float]  # {category: preference_score}
    next_video_prediction: Optional[str] = None  # Next recommended category
    personalization_score: float = 0.0


# ============================================================================
# REAL-TIME EVENT STREAMING (SSE)
# ============================================================================

@router.get("/stream/ml-feedback")
async def stream_ml_feedback(
    request: Request,
    user_id: str = Query(...)
):
    """
    Server-Sent Events (SSE) stream for real-time ML feedback.

    Frontend subscribes to this endpoint and receives instant updates when:
    - User swipes on a video
    - ML algorithm updates user preferences
    - Next video recommendation changes

    Args:
        request: FastAPI request (for connection check)
        user_id: User ID to stream feedback for

    Returns:
        SSE stream of ML feedback events
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            redis = await get_redis()
            pubsub = redis.pubsub()

            # Subscribe to user's ML feedback channel
            channel = f"ml_feedback:{user_id}"
            await pubsub.subscribe(channel)

            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"

            # Listen for messages
            async for message in pubsub.listen():
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from ML feedback stream: {user_id}")
                    break

                if message["type"] == "message":
                    # Forward ML feedback to frontend
                    yield f"data: {message['data']}\n\n"

        except asyncio.CancelledError:
            logger.info(f"ML feedback stream cancelled for {user_id}")
        except Exception as e:
            logger.error(f"Error in ML feedback stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# REAL-TIME EVENT LOGGING WITH ML FEEDBACK
# ============================================================================

@router.post("/stream/event")
async def log_event_with_feedback(event: RealtimeEvent):
    """
    Log event and instantly return ML feedback.

    TikTok-style real-time loop:
    1. User swipes on video
    2. Event logged to database
    3. ML algorithm updates user preferences
    4. Feedback published to SSE stream
    5. Frontend receives instant update

    Args:
        event: Event from frontend

    Returns:
        ML feedback with updated preferences
    """
    try:
        start_time = time.time()
        async_db = getattr(db_client, "async_db", None)

        if not async_db:
            return {"error": "Database not connected"}

        # Build event data
        event_data = {
            "user_id": event.user_id,
            "video_id": event.video_id,
            "event_type": event.event_type,
            "watch_ratio": event.watch_ratio,
            "category": event.category,
            "timestamp": event.timestamp or time.time()
        }

        # Log event (updates stats in real-time)
        await log_event(async_db, event_data)

        # Get updated user preferences
        user_result = await async_db.query(f"SELECT * FROM {event.user_id}")

        if not user_result or not user_result[0]["result"]:
            return {"error": "User not found"}

        user = user_result[0]["result"][0]

        # Extract category preferences
        category_prefs = user.get("category_preferences", {})

        # Calculate preference scores
        updated_preferences = {}
        for cat, stats in category_prefs.items():
            impressions = stats.get("impressions", 0)
            avg_watch = stats.get("avg_watch_ratio", 0)
            like_rate = stats.get("like_rate", 0)

            # Simple preference score
            if impressions > 0:
                preference_score = (avg_watch * 0.7 + like_rate * 0.3)
                updated_preferences[cat] = round(preference_score, 3)

        # Predict next recommended category
        next_category = None
        if updated_preferences:
            next_category = max(updated_preferences, key=updated_preferences.get)

        # Calculate overall personalization score
        personalization_score = 0.0
        if updated_preferences:
            personalization_score = sum(updated_preferences.values()) / len(updated_preferences)

        # Build ML feedback
        feedback = MLFeedback(
            user_id=event.user_id,
            event_type=event.event_type,
            video_id=event.video_id,
            category=event.category,
            updated_preferences=updated_preferences,
            next_video_prediction=next_category,
            personalization_score=round(personalization_score, 3)
        )

        # Publish feedback to Redis for SSE stream
        await publish_event(
            channel=f"ml_feedback:{event.user_id}",
            event_data={
                "type": "ml_update",
                "feedback": feedback.model_dump(),
                "timestamp": time.time()
            }
        )

        elapsed = time.time() - start_time
        logger.info(
            f"Event logged with ML feedback for {event.user_id}: "
            f"{event.event_type} on {event.category}, {elapsed:.3f}s"
        )

        return feedback

    except Exception as e:
        logger.error(f"Error logging event with feedback: {e}")
        return {"error": str(e)}


# ============================================================================
# EVENT BUFFER - High-volume event batching
# ============================================================================

class EventBuffer:
    """
    Buffer for high-volume events.

    TikTok can process millions of events per second.
    This buffer batches events for efficient database writes.
    """

    def __init__(self, flush_interval: float = 1.0, batch_size: int = 100):
        """
        Initialize event buffer.

        Args:
            flush_interval: Seconds between flushes
            batch_size: Max events per batch
        """
        self.buffer: Dict[str, list] = {}  # {user_id: [events]}
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self.last_flush = time.time()
        self.lock = asyncio.Lock()

    async def add_event(self, user_id: str, event: Dict[str, Any]):
        """
        Add event to buffer.

        Args:
            user_id: User ID
            event: Event data
        """
        async with self.lock:
            if user_id not in self.buffer:
                self.buffer[user_id] = []

            self.buffer[user_id].append(event)

            # Flush if batch size reached
            if len(self.buffer[user_id]) >= self.batch_size:
                await self.flush_user(user_id)

    async def flush_user(self, user_id: str):
        """
        Flush events for a user.

        Args:
            user_id: User ID
        """
        if user_id not in self.buffer or not self.buffer[user_id]:
            return

        events = self.buffer[user_id]
        self.buffer[user_id] = []

        # Batch insert to database
        async_db = getattr(db_client, "async_db", None)
        if async_db:
            for event in events:
                await log_event(async_db, event)

        logger.info(f"Flushed {len(events)} buffered events for {user_id}")

    async def flush_all(self):
        """Flush all buffered events."""
        async with self.lock:
            for user_id in list(self.buffer.keys()):
                await self.flush_user(user_id)

        self.last_flush = time.time()

    async def auto_flush_loop(self):
        """Background task to auto-flush events periodically."""
        while True:
            await asyncio.sleep(self.flush_interval)

            if time.time() - self.last_flush >= self.flush_interval:
                await self.flush_all()


# Global event buffer
event_buffer = EventBuffer(flush_interval=1.0, batch_size=100)


@router.post("/stream/event/buffered")
async def log_event_buffered(event: RealtimeEvent):
    """
    Log event to buffer (high-volume mode).

    For extreme scale (like TikTok), buffer events and batch-write.

    Args:
        event: Event from frontend

    Returns:
        Success status
    """
    try:
        event_data = {
            "user_id": event.user_id,
            "video_id": event.video_id,
            "event_type": event.event_type,
            "watch_ratio": event.watch_ratio,
            "category": event.category,
            "timestamp": event.timestamp or time.time()
        }

        # Add to buffer (will be flushed automatically)
        await event_buffer.add_event(event.user_id, event_data)

        return {
            "success": True,
            "buffered": True,
            "message": "Event added to buffer"
        }

    except Exception as e:
        logger.error(f"Error buffering event: {e}")
        return {"error": str(e)}


# ============================================================================
# STARTUP/SHUTDOWN - Event buffer lifecycle
# ============================================================================

@router.on_event("startup")
async def start_event_buffer():
    """Start event buffer auto-flush loop."""
    asyncio.create_task(event_buffer.auto_flush_loop())
    logger.info("Event buffer auto-flush started")


@router.on_event("shutdown")
async def stop_event_buffer():
    """Flush remaining events on shutdown."""
    await event_buffer.flush_all()
    logger.info("Event buffer flushed on shutdown")
