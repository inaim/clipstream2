import os
import requests
from typing import Optional, Any, List

SURREAL_URL = os.environ.get('SURREALDB_URL')
SURREAL_USER = os.environ.get('SURREALDB_USER')
SURREAL_PASS = os.environ.get('SURREALDB_PASS')


def _headers():
    headers = {}
    if SURREAL_USER and SURREAL_PASS:
        # Basic auth via requests will handle it; leave headers empty
        pass
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    return headers


def _auth():
    if SURREAL_USER and SURREAL_PASS:
        return (SURREAL_USER, SURREAL_PASS)
    return None


def is_available() -> bool:
    return bool(SURREAL_URL)


def exec_sql(sql: str) -> Any:
    if not SURREAL_URL:
        raise RuntimeError('SURREALDB_URL not configured')
    resp = requests.post(f"{SURREAL_URL}/sql", data=sql, headers=_headers(), auth=_auth(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def select_videos(limit: int = 50, offset: int = 0) -> List[dict]:
    sql = f"SELECT * FROM video ORDER BY created_at DESC LIMIT {limit} OFFSET {offset};"
    res = exec_sql(sql)
    # Surreal returns a list of results per statement; simplify extraction
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return []


def get_video(video_id: int) -> Optional[dict]:
    sql = f"SELECT * FROM video WHERE id = {video_id} LIMIT 1;"
    res = exec_sql(sql)
    if isinstance(res, list) and len(res) > 0 and len(res[0]) > 0:
        return res[0][0]
    return None
