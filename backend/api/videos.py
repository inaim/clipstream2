from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from db.surrealdb_client import db_client
from utils.config import settings
from utils.auth import get_current_user

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
    try:
        await pubsub.subscribe(channel)
    except Exception as e:
        # Surface a single error frame then end the stream
        yield f"data: {{\"error\": \"redis_subscribe_failed\", \"detail\": \"{str(e)}\"}}\n\n"
        try:
            await redis.close()
        except Exception:
            pass
        return

    try:
        while True:
            try:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=10)
            except Exception as e:
                # Connection dropped; emit error and break to avoid crashing the request
                yield f"data: {{\"error\": \"redis_connection_reset\", \"detail\": \"{str(e)}\"}}\n\n"
                break

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


class LLMVerificationPayload(BaseModel):
    verdict: Literal["approved", "flagged", "rejected"] = Field(
        ...,
        description="Final moderation verdict returned by the LLM/MCP pipeline"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized confidence score reported by the verifier"
    )
    summary: str = Field(
        ...,
        max_length=500,
        description="Short explanation of the verdict"
    )
    mcp_run_id: Optional[str] = Field(
        default=None,
        description="Identifier returned by the MCP job that orchestrated the verification"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional structured metadata (labels, keyword hits, etc.)"
    )


@router.post('/videos/{video_id}/llm-verification')
async def attach_llm_verification(
    video_id: str,
    payload: LLMVerificationPayload,
    current_user_id: str = Depends(get_current_user)
):
    """Persist the result of the LLM/MCP verification pipeline and broadcast it to listeners."""
    video = await db_client.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail='Not Found')

    owner_id = ""
    try:
        owner_id = str(video.get('user_id') or video.get('user') or "")
    except Exception:
        owner_id = ""

    allowed_callers = set()
    if owner_id:
        allowed_callers.add(owner_id)
    mcp_service_account = getattr(settings, 'MCP_SERVICE_ACCOUNT_ID', None)
    if mcp_service_account:
        allowed_callers.add(mcp_service_account)

    if allowed_callers and current_user_id not in allowed_callers:
        raise HTTPException(status_code=403, detail="Only the uploader or the MCP verifier can mark this video")

    verification = {
        "verdict": payload.verdict,
        "confidence": payload.confidence,
        "summary": payload.summary,
        "mcp_run_id": payload.mcp_run_id,
        "metadata": payload.metadata or {},
        "reviewed_by": current_user_id
    }

    status_map = {
        "approved": "active",
        "flagged": "flagged",
        "rejected": "blocked"
    }
    target_status = status_map.get(payload.verdict)

    update_fields: Dict[str, object] = {
        "llm_verification": verification
    }
    if target_status:
        update_fields["status"] = target_status

    updated = await db_client.update_video_fields(video_id, update_fields)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to record verification state")

    # Broadcast an SSE/Redis event so subscribed clients see the moderation update
    try:
        import json as _json
        import redis as redis_sync

        if settings.REDIS_URL:
            payload_json = _json.dumps({
                "type": "llm_verification",
                "video_id": video_id,
                "verdict": payload.verdict,
                "status": target_status,
                "mcp_run_id": payload.mcp_run_id,
                "confidence": payload.confidence
            })
            channel = f"video:{video_id}:events"
            try:
                r = redis_sync.from_url(settings.REDIS_URL)
                r.publish(channel, payload_json)
            except Exception:
                pass
    except Exception:
        # Non-blocking best-effort notification
        pass

    return {
        "video_id": video_id,
        "status": target_status or video.get("status"),
        "llm_verification": verification
    }
