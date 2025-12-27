from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from db.surrealdb_client import db_client

router = APIRouter()


class FollowPayload(BaseModel):
    follower_id: str
    following_id: str


def _normalize_user_id(user_id: str) -> str:
    """Return the raw record id portion (strip 'user:' if present)."""
    user_id_str = str(user_id)
    if user_id_str.startswith("user:"):
        return user_id_str.split(":", 1)[1]
    return user_id_str


def _qualify_user(user_id: str) -> str:
    """Convert raw ids to Surreal record references."""
    normalized = _normalize_user_id(user_id)
    return f"user:{normalized}"


def _extract_results(result: Any) -> List[Dict[str, Any]]:
    """Handle SurrealDB SDK response shapes and return a list of rows."""
    if not result:
        return []
    first = result[0]
    if isinstance(first, dict) and "result" in first:
        return first.get("result") or []
    if isinstance(first, list):
        return first
    if isinstance(first, dict):
        return [first]
    return []


def _shape_follow_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a stable JSON shape for follow edges."""
    shaped: Dict[str, Any] = {}
    if record.get("id") is not None:
        shaped["id"] = str(record.get("id"))
    # Surreal uses 'in' and 'out' to point to the connected records
    if "in" in record:
        shaped["follower_id"] = str(record["in"])
    if "out" in record:
        shaped["following_id"] = str(record["out"])
    if "created_at" in record and record.get("created_at") is not None:
        shaped["created_at"] = record["created_at"]
    return shaped


@router.get("/follows")
async def list_follows(
    follower_id: Optional[str] = Query(None, description="Filter by follower id (user:xyz or raw id)"),
    following_id: Optional[str] = Query(None, description="Filter by following id (user:xyz or raw id)"),
):
    """Fetch follow relationships. Returns a JSON array."""
    try:
        filters = []
        params: Dict[str, str] = {}

        if follower_id:
            params["follower_id"] = _normalize_user_id(follower_id)
            filters.append("in = type::thing('user', $follower_id)")
        if following_id:
            params["following_id"] = _normalize_user_id(following_id)
            filters.append("out = type::thing('user', $following_id)")

        where_clause = " AND ".join(filters) if filters else "true"
        result = await db_client.query(
            f"SELECT id, in, out, created_at FROM follows WHERE {where_clause}",
            params,
        )
        rows = _extract_results(result)
        shaped = [_shape_follow_record(r) for r in rows]
        return shaped
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch follows: {e}")


@router.post("/follows")
async def create_follow(payload: FollowPayload):
    """Create a follow edge from follower -> following. Idempotent."""
    follower_ref = _qualify_user(payload.follower_id)
    following_ref = _qualify_user(payload.following_id)

    if follower_ref == following_ref:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    params = {
        "follower": follower_ref.split(":", 1)[1],
        "following": following_ref.split(":", 1)[1],
    }

    try:
        # If the relation already exists, return it instead of duplicating
        existing = await db_client.query(
            """
            SELECT id, in, out, created_at FROM follows
            WHERE in = type::thing('user', $follower) AND out = type::thing('user', $following)
            """,
            params,
        )
        existing_rows = _extract_results(existing)
        if existing_rows:
            return {"success": True, "data": _shape_follow_record(existing_rows[0])}

        result = await db_client.query(
            """
            RELATE type::thing('user', $follower) -> follows -> type::thing('user', $following)
            SET created_at = time::now()
            """,
            params,
        )
        rows = _extract_results(result)
        record = _shape_follow_record(rows[0]) if rows else None
        return {"success": True, "data": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create follow: {e}")


@router.delete("/follows")
async def delete_follow(payload: FollowPayload):
    """Remove a follow edge."""
    params = {
        "follower": _normalize_user_id(payload.follower_id),
        "following": _normalize_user_id(payload.following_id),
    }

    try:
        result = await db_client.query(
            """
            DELETE follows WHERE in = type::thing('user', $follower)
            AND out = type::thing('user', $following)
            """,
            params,
        )
        rows = _extract_results(result)
        return {"success": True, "removed": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete follow: {e}")
