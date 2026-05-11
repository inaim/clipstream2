from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()


class CommentCreate(BaseModel):
    video_id: str
    content: str
    parent_id: Optional[str] = None


@router.get("/comments")
async def list_comments(video_id: str = Query(..., description="Video record id e.g. video:abc")):
    """Return all comments for a video."""
    try:
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        result = await async_db.query(
            "SELECT * FROM comment WHERE video_id = type::thing('video', $vid) ORDER BY created_at DESC",
            {"vid": video_id.split(":", 1)[1] if ":" in video_id else video_id},
        )
        rows: List[Dict[str, Any]] = []
        if result and isinstance(result[0], dict) and "result" in result[0]:
            rows = result[0]["result"] or []
        elif result and isinstance(result[0], list):
            rows = result[0]
        return rows
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comments: {e}")


@router.post("/comments")
async def create_comment(payload: CommentCreate, current_user_id: str = Depends(get_current_user)):
    """Create a new comment."""
    try:
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        res = await async_db.query(
            """
            CREATE comment CONTENT {
                video_id: type::thing('video', $vid),
                user_id: type::thing('user', $user),
                content: $content,
                parent_id: $parent,
                created_at: time::now()
            }
            """,
            {
                "vid": payload.video_id.split(":", 1)[1] if ":" in payload.video_id else payload.video_id,
                "user": current_user_id.split(":", 1)[1] if ":" in current_user_id else current_user_id,
                "content": payload.content,
                "parent": payload.parent_id.split(":", 1)[1] if payload.parent_id and ":" in payload.parent_id else payload.parent_id,
            },
        )
        if res and isinstance(res[0], dict) and "result" in res[0] and res[0]["result"]:
            return res[0]["result"][0]
        if res and isinstance(res[0], list) and res[0]:
            return res[0][0]
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {e}")


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user_id: str = Depends(get_current_user)):
    """Delete a comment by id (author or admin can enforce additional checks if desired)."""
    try:
        async_db = getattr(db_client, "async_db", None)
        if not async_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        res = await async_db.query(
            "DELETE comment WHERE id = type::thing('comment', $cid)",
            {"cid": comment_id.split(":", 1)[1] if ":" in comment_id else comment_id},
        )
        deleted = 0
        if res and isinstance(res[0], dict) and "result" in res[0]:
            deleted = len(res[0].get("result") or [])
        elif res and isinstance(res[0], list):
            deleted = len(res[0])
        return {"success": True, "removed": deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete comment: {e}")
