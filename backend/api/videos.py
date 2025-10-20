from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List
from db.surrealdb_client import db_client
from utils.config import settings

router = APIRouter()


async def _sse_event_generator(channel: str):
    """Async generator that yields server-sent events from Redis channel."""
    # Try aioredis first, but some environments/versions of aioredis have
    # import-time errors on newer Pythons. Fall back to redis.asyncio which
    # provides a very similar interface for our use-case.
    try:
        import aioredis as _aioredis
        redis_client = _aioredis.from_url
    except Exception:
        try:
            import redis.asyncio as _rasync
            redis_client = _rasync.from_url
        except Exception:
            yield "data: {\"error\": \"aioredis/redis.asyncio not available\"}\n\n"
            return

    if not settings.REDIS_URL:
        yield "data: {\"error\": \"REDIS_URL not configured\"}\n\n"
        return

    redis = redis_client(settings.REDIS_URL)
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=10)
            if msg is None:
                # keep-alive comment
                yield ":\n\n"
                continue
            data = msg.get('data')
            if isinstance(data, bytes):
                try:
                    data = data.decode()
                except Exception:
                    data = str(data)
            # Emit as SSE 'data:' frame
            yield f"data: {data}\n\n"
    finally:
        try:
            await pubsub.unsubscribe(channel)
        except Exception:
            pass
        try:
            await redis.close()
        except Exception:
            pass


@router.get('/videos')
async def list_videos(limit: int = 50, offset: int = 0):
    """List videos (compatibility endpoint used by frontend). Returns a JSON array."""
    videos = await db_client.get_for_you_feed(limit)
    # db_client.get_for_you_feed returns a list; ensure we return an array
    return videos or []


@router.get('/videos/events/global')
async def videos_global_events(request: Request):
    """SSE endpoint for global video events (new uploads, global updates)."""
    channel = "videos:events"

    async def event_stream():
        async for chunk in _sse_event_generator(channel):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(event_stream(), media_type='text/event-stream')


@router.get('/videos/{video_id}')
async def get_video(video_id: str):
    video = await db_client.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail='Not Found')
    return video


@router.get('/videos/{video_id}/events')
async def video_events(request: Request, video_id: str):
    """Server-Sent Events endpoint that streams events for a specific video.

    The endpoint subscribes to Redis pub/sub channel `video:{video_id}:events` and
    forwards messages as SSE frames. If Redis or aioredis is not configured,
    it returns a single error message and closes the stream.
    """
    channel = f"video:{video_id}:events"

    async def event_stream():
        async for chunk in _sse_event_generator(channel):
            # If client disconnects, break
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(event_stream(), media_type='text/event-stream')
