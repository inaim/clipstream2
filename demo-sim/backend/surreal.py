import os
import time
import json
import logging
from typing import Optional, Any, List
import requests

SURREAL_URL = os.environ.get('SURREALDB_URL')
SURREAL_USER = os.environ.get('SURREALDB_USER')
SURREAL_PASS = os.environ.get('SURREALDB_PASS')
SURREAL_NS = os.environ.get('SURREALDB_NS')
SURREAL_DB = os.environ.get('SURREALDB_DB')

LOG = logging.getLogger('surreal')
LOG.setLevel(logging.INFO)


def _headers():
    # Surreal accepts raw SQL in the body; set a sensible content type
    return { 'Content-Type': 'text/plain; charset=utf-8' }


def _auth():
    if SURREAL_USER and SURREAL_PASS:
        return (SURREAL_USER, SURREAL_PASS)
    return None


def is_available() -> bool:
    return bool(SURREAL_URL)


def _safe_literal(val: Any) -> str:
    # Convert Python value into a Surreal-friendly literal using JSON encoding for strings
    # Numbers, booleans, and null will be preserved as JSON literals
    return json.dumps(val)


def exec_sql(sql: str, retries: int = 3, timeout: int = 10) -> Any:
    if not SURREAL_URL:
        raise RuntimeError('SURREALDB_URL not configured')
    attempt = 0
    last_err = None
    while attempt < retries:
        try:
            LOG.debug('exec_sql attempt %s: %s', attempt + 1, sql)
            url = f"{SURREAL_URL}/sql"
            params = {}
            if SURREAL_NS:
                params['ns'] = SURREAL_NS
            if SURREAL_DB:
                params['db'] = SURREAL_DB
            resp = requests.post(url, data=sql, headers=_headers(), auth=_auth(), timeout=timeout, params=params)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                # Not JSON? return text
                return resp.text
        except Exception as e:
            # If requests produced a response, include body for debugging
            last_err = e
            try:
                text = getattr(e, 'response', None)
                if text is not None and hasattr(text, 'text'):
                    LOG.debug('surreal response body: %s', text.text)
            except Exception:
                pass
            wait = (2 ** attempt) * 0.2
            LOG.warning('surreal exec_sql failed (attempt %s/%s): %s; retrying in %.2fs', attempt + 1, retries, str(e), wait)
            time.sleep(wait)
            attempt += 1
    LOG.error('surreal exec_sql failed after %s attempts: %s', retries, last_err)
    raise last_err


def select_videos(limit: int = 50, offset: int = 0) -> List[dict]:
    sql = f"SELECT * FROM video ORDER BY created_at DESC LIMIT {int(limit)} OFFSET {int(offset)};"
    res = exec_sql(sql)
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    return []


def get_video(video_id: int) -> Optional[dict]:
    sql = f"SELECT * FROM video WHERE id = {int(video_id)} LIMIT 1;"
    res = exec_sql(sql)
    if isinstance(res, list) and len(res) > 0 and len(res[0]) > 0:
        return res[0][0]
    return None


def insert_person(user_id: int, email: str, display_name: str = '') -> Any:
    content = {'id': int(user_id), 'email': email, 'display_name': display_name}
    sql = f"INSERT person CONTENT {json.dumps(content)};"
    return exec_sql(sql)


def insert_video(video_id: int, owner_id: int, title: str, filename: str, content_hash: str) -> Any:
    content = {'id': int(video_id), 'owner_id': int(owner_id), 'title': title, 'filename': filename, 'content_hash': content_hash, 'created_at': {"time": "now"}}
    # created_at will be handled server-side in Surreal; include a placeholder if desired
    sql = f"INSERT video CONTENT {json.dumps(content)};"
    return exec_sql(sql)


def create_user(email: str, display_name: str = '') -> int:
    content = {'email': email, 'display_name': display_name}
    sql = f"INSERT person CONTENT {json.dumps(content)} RETURN id;"
    res = exec_sql(sql)
    try:
        return res[0][0]['id']
    except Exception:
        return -1


def create_video(owner_id: int, title: str, filename: str, content_hash: str) -> int:
    content = {'owner_id': int(owner_id), 'title': title, 'filename': filename, 'content_hash': content_hash}
    sql = f"INSERT video CONTENT {json.dumps(content)} RETURN id;"
    res = exec_sql(sql)
    try:
        return res[0][0]['id']
    except Exception:
        return -1


def update_video_filename(video_id: int, filename: str, status: str = 'ready') -> Any:
    # Use json.dumps to safely quote the filename and status
    fn = json.dumps(filename)
    st = json.dumps(status)
    sql = f"UPDATE video SET filename = {fn}, status = {st} WHERE id = {int(video_id)};"
    return exec_sql(sql)
