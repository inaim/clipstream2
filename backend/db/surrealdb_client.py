from surrealdb import AsyncSurreal
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Union
import threading
from utils.config import settings

logger = logging.getLogger(__name__)

class SurrealDBClient:
    def __init__(self):
        self.db: Optional[AsyncSurreal] = None
        self._connected = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        # Ensure _loop always exists to avoid attribute errors when called
        # from synchronous worker processes that skipped connect().
        self._loop = None
    
    async def connect(self):
        if not self._connected:
            try:
                self.db = AsyncSurreal(settings.SURREALDB_URL)
                await self.db.connect()

                # Capture the running event loop so synchronous callers (worker tasks)
                # can schedule coroutines onto the same loop using
                # asyncio.run_coroutine_threadsafe. This is only valid if connect
                # is called from the worker process after forking (worker init).
                try:
                    self._loop = asyncio.get_running_loop()
                except Exception:
                    self._loop = None

                # Different authentication for development vs production
                if settings.ENVIRONMENT == "production":
                    # Production: Sign in with namespace-level credentials (SurrealDB Cloud)
                    logger.info(f"[SURREALDB] Production mode: Using namespace-level auth")
                    await self.db.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS,
                        "namespace": settings.SURREALDB_NS
                    })
                else:
                    # Development: Sign in with root-level credentials (local SurrealDB)
                    logger.info(f"[SURREALDB] Development mode: Using root-level auth")
                    await self.db.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS
                    })

                # Use the namespace and database
                await self.db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
                self._connected = True
                logger.info("✅ Connected to SurrealDB")
            except Exception as e:
                logger.error(f"❌ Connection failed: {e}")
                raise
    
    async def disconnect(self):
        if self._connected and self.db:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, self.db.close)
            except:
                pass
            self._connected = False

    def sync_get_video(self, video_id: str) -> Optional[Dict]:
        """Synchronous wrapper for get_video using the client's running loop.
        Falls back to running the async method via asyncio.run if no loop is
        available (not recommended in worker processes where persistent loop
        exists).
        """
        try:
            loop = getattr(self, '_loop', None)
            if loop:
                # If the client was connected and captured a loop, use thread-safe submission
                fut = asyncio.run_coroutine_threadsafe(self.get_video(video_id), loop)
                return fut.result(timeout=10)
            # Otherwise run the coroutine freshly (safe in synchronous Celery tasks)
            return asyncio.run(self.get_video(video_id))
        except Exception as e:
            logger.error(f"sync_get_video error: {e}")
            return None

    def sync_update_video_fields(self, video_id: str, fields: Dict) -> bool:
        """Synchronous wrapper for update_video_fields using the client's loop."""
        try:
            loop = getattr(self, '_loop', None)
            if loop:
                fut = asyncio.run_coroutine_threadsafe(self.update_video_fields(video_id, fields), loop)
                return fut.result(timeout=10)
            return asyncio.run(self.update_video_fields(video_id, fields))
        except Exception as e:
            logger.error(f"sync_update_video_fields error: {e}")
            return False
    
    async def create_user(self, email: str, password_hash: str, display_name: str = None) -> Dict:
        # Directly await AsyncSurreal.create since it's async
        result = await self.db.create("user", {
            "email": email,
            "password_hash": password_hash,
            "display_name": display_name or email.split("@")[0],
            "watch_tokens": 0,
            "watch_tokens_pending": 0
        })
        return result if result else None

    async def query(self, sql: str, params: Optional[Dict] = None):
        """Thin wrapper so callers don't reach into db_client.db directly."""
        if self._connected and self.db:
            return await self.db.query(sql, params or {})
        # Fallback: create a short-lived client if connect() wasn't called (dev-only)
        try:
            tmp = AsyncSurreal(settings.SURREALDB_URL)
            await tmp.connect()
            if settings.ENVIRONMENT == "production":
                await tmp.signin({
                    "username": settings.SURREALDB_USER,
                    "password": settings.SURREALDB_PASS,
                    "namespace": settings.SURREALDB_NS
                })
            else:
                await tmp.signin({
                    "username": settings.SURREALDB_USER,
                    "password": settings.SURREALDB_PASS,
                })
            await tmp.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
            return await tmp.query(sql, params or {})
        finally:
            try:
                await tmp.close()
            except Exception:
                pass
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        try:
            result = await self.db.query(
                "SELECT * FROM user WHERE email = $email LIMIT 1",
                {"email": email}
            )
            logger.info(f"get_user_by_email result type: {type(result)}, result: {result}")
            if result and len(result) > 0:
                # Check if result has 'result' key or is a direct list
                if isinstance(result[0], dict) and 'result' in result[0]:
                    user = result[0]['result'][0] if result[0]['result'] else None
                    logger.info(f"get_user_by_email returning (dict): {user}")
                    return user
                elif isinstance(result[0], list):
                    user = result[0][0] if result[0] else None
                    logger.info(f"get_user_by_email returning (list): {user}")
                    return user
                else:
                    logger.info(f"get_user_by_email returning (direct): {result[0]}")
                    return result[0] if result[0] else None
            logger.info(f"get_user_by_email returning None")
            return None
        except Exception as e:
            logger.error(f"Error parsing get_user_by_email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        try:
            # Parse the user_id to extract table and record_id
            # Format is typically "table:record_id" e.g. "user:wmzyfkqkg2ojcubnmzvv"
            if ':' in user_id:
                table, record_id = user_id.split(':', 1)
            else:
                # If no colon, assume it's just the record_id and table is 'user'
                table = 'user'
                record_id = user_id

            logger.info(f"get_user_by_id: table={table}, record_id={record_id}")

            # Use query to fetch the specific record
            result = await self.db.query(
                f"SELECT * FROM {table} WHERE id = type::thing($table, $record_id)",
                {"table": table, "record_id": record_id}
            )
            logger.info(f"get_user_by_id query result type: {type(result)}, result: {result}")

            # Parse the result - same logic as get_user_by_email
            if result and len(result) > 0:
                if isinstance(result[0], dict) and 'result' in result[0]:
                    user = result[0]['result'][0] if result[0]['result'] else None
                    logger.info(f"get_user_by_id returning (dict): {user}")
                    return user
                elif isinstance(result[0], list):
                    user = result[0][0] if result[0] else None
                    logger.info(f"get_user_by_id returning (list): {user}")
                    return user
                else:
                    logger.info(f"get_user_by_id returning (direct): {result[0]}")
                    return result[0] if isinstance(result[0], dict) else None

            logger.info(f"get_user_by_id returning None")
            return None
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {e}")
            return None
    
    async def create_video(self, user_id: str, title: str, cdn_url: str, **kwargs) -> Dict:
        try:
            result = await self.db.create("video", {
                "title": title,
                "cdn_url": cdn_url,
                "status": "active",
                **kwargs
            })

            # SurrealDB client may return different shapes depending on version:
            # - a list where first element is the created record (dict)
            # - a dict with a 'result' key
            # - a direct dict representing the created record
            created = None
            try:
                if isinstance(result, list) and len(result) > 0:
                    item = result[0]
                    if isinstance(item, dict) and 'result' in item:
                        created = item['result'][0] if item['result'] else None
                    elif isinstance(item, dict) and 'id' in item:
                        created = item
                    elif isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
                        created = item[0]
                    else:
                        created = item
                elif isinstance(result, dict):
                    if 'result' in result and isinstance(result['result'], list) and len(result['result'])>0:
                        created = result['result'][0]
                    else:
                        created = result
                else:
                    created = None
            except Exception:
                created = None

            if not created or not isinstance(created, dict):
                raise RuntimeError(f"Unexpected create() response from SurrealDB: {result}")

            # Find id in created record (support multiple possible key names)
            vid = created.get('id') or created.get('ID') or created.get('_id') or created.get('record')
            if not vid:
                # If Surreal returned the full thing value, try to extract from 'id' present in nested shapes
                # Fallback to stringifying the created object to ensure we don't pass None into RELATE.
                vid = created.get('id') if isinstance(created.get('id'), str) else None

            if vid:
                try:
                    await self.db.query(
                        "RELATE $user->created_by->$video",
                        {"user": user_id, "video": vid}
                    )
                except Exception as e:
                    logger.warning(f"Failed to create relation user->video: {e} (video id={vid})")

            return created
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            raise
    
    async def get_video(self, video_id: str) -> Optional[Dict]:
        try:
            # If we have a persistent connected AsyncSurreal instance, use it.
            if self._connected and self.db:
                result = await self.db.query(
                    "SELECT *, <-created_by<-user.* AS creator FROM $video",
                    {"video": video_id}
                )
            else:
                # Otherwise create a temporary AsyncSurreal client for this call
                from surrealdb import AsyncSurreal
                tmp = AsyncSurreal(settings.SURREALDB_URL)
                await tmp.connect()
                if settings.ENVIRONMENT == "production":
                    await tmp.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS,
                        "namespace": settings.SURREALDB_NS,
                    })
                else:
                    await tmp.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS,
                    })
                await tmp.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
                try:
                    result = await tmp.query(
                        "SELECT *, <-created_by<-user.* AS creator FROM $video",
                        {"video": video_id}
                    )
                finally:
                    try:
                        await tmp.close()
                    except Exception:
                        pass
            # Debug: log raw result shape to diagnose worker lookup failures
            try:
                logger.debug(f"get_video raw query result for {video_id}: type={type(result)}, value={result}")
            except Exception:
                # Never let logging failure break the query flow
                logger.debug(f"get_video raw query result for {video_id}: (unserializable result)")
            # The AsyncSurreal client may return different shapes. Normalize safely.
            if not result:
                # Fallback: try querying by table + record id using type::thing()
                try:
                    if ':' in video_id:
                        table, record_id = video_id.split(':', 1)
                    else:
                        table = 'video'
                        record_id = video_id

                    logger.debug(f"get_video fallback query using table={table}, record_id={record_id}")

                    # Use persistent client if present
                    if self._connected and self.db:
                        result = await self.db.query(
                            "SELECT *, <-created_by<-user.* AS creator FROM $table WHERE id = type::thing($table, $record_id)",
                            {"table": table, "record_id": record_id}
                        )
                    else:
                        from surrealdb import AsyncSurreal
                        tmp2 = AsyncSurreal(settings.SURREALDB_URL)
                        await tmp2.connect()
                        if settings.ENVIRONMENT == "production":
                            await tmp2.signin({
                                "username": settings.SURREALDB_USER,
                                "password": settings.SURREALDB_PASS,
                                "namespace": settings.SURREALDB_NS,
                            })
                        else:
                            await tmp2.signin({
                                "username": settings.SURREALDB_USER,
                                "password": settings.SURREALDB_PASS,
                            })
                        await tmp2.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
                        try:
                            result = await tmp2.query(
                                "SELECT *, <-created_by<-user.* AS creator FROM $table WHERE id = type::thing($table, $record_id)",
                                {"table": table, "record_id": record_id}
                            )
                        finally:
                            try:
                                await tmp2.close()
                            except Exception:
                                pass

                    if not result:
                        return None
                except Exception as e:
                    logger.debug(f"get_video fallback query failed for {video_id}: {e}")
                    return None
            first = result[0]
            # If client returns a dict with 'result' key
            if isinstance(first, dict) and 'result' in first:
                res_list = first.get('result') or []
                record = res_list[0] if res_list else None
                # Normalize RecordID objects to strings for safe serialization
                if isinstance(record, dict) and record.get('id') is not None:
                    try:
                        record['id'] = str(record['id'])
                    except Exception:
                        pass
                return record
            # If client returns a list whose first element is a list of records
            if isinstance(first, list):
                record = first[0] if first else None
                if isinstance(record, dict) and record.get('id') is not None:
                    try:
                        record['id'] = str(record['id'])
                    except Exception:
                        pass
                return record
            # Fallback: if it's a dict representing the record
            if isinstance(first, dict):
                if first.get('id') is not None:
                    try:
                        first['id'] = str(first['id'])
                    except Exception:
                        pass
                return first
            return None
        except Exception as e:
            logger.error(f"Error getting video: {e}")
            return None

    async def update_video_fields(self, video_id: str, fields: Dict) -> bool:
        """
        Safely update arbitrary fields on a video record using a read-modify-write
        pattern. Merges `processing_steps` dictionaries where appropriate.
        Returns True on success, False if the record was not found.
        """
        try:
            # Build SET clauses and params directly from provided fields. For
            # simplicity we accept the provided `processing_steps` as authoritative
            # (no server-side merge) to avoid an extra read which can race.
            params = {}
            set_clauses = []

            for key, value in fields.items():
                params[key] = value
                set_clauses.append(f"{key} = ${key}")

            if not set_clauses:
                logger.info("update_video_fields: no fields to update")
                return True

            params['id'] = video_id
            set_sql = ", ".join(set_clauses)

            # Use persistent client if present
            if self._connected and self.db:
                await self.db.query(f"UPDATE video SET {set_sql} WHERE id = $id", params)
            else:
                # Temporary client path
                from surrealdb import AsyncSurreal
                tmp = AsyncSurreal(settings.SURREALDB_URL)
                await tmp.connect()
                if settings.ENVIRONMENT == "production":
                    await tmp.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS,
                        "namespace": settings.SURREALDB_NS,
                    })
                else:
                    await tmp.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS,
                    })
                await tmp.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
                try:
                    await tmp.query(f"UPDATE video SET {set_sql} WHERE id = $id", params)
                finally:
                    try:
                        await tmp.close()
                    except Exception:
                        pass

            return True
        except Exception as e:
            # Don't raise here; surface failure as a False return to callers so
            # Celery tasks can handle retries and we avoid crashing the worker.
            logger.error(f"Error updating video {video_id}: {e}")
            return False
    
    async def earn_tokens(self, user_id: str, amount: int, reason: str, video_id: str = None) -> Dict:
        try:
            earning = await self.db.create("earning", {
                "creator": user_id,
                "amount": amount,
                "reason": reason,
                "video": video_id,
                "settled_on_chain": False
            })
            await self.db.query(
                "UPDATE $user SET watch_tokens_pending += $amount",
                {"user": user_id, "amount": amount}
            )
            # SurrealDB create returns the created record directly
            return earning
        except Exception as e:
            logger.error(f"Error earning tokens: {e}")
            raise
    
    async def get_for_you_feed(self, limit: int = 50) -> List[Dict]:
        try:
            # Include in-progress uploads (queued/processing) so users see their
            # newly uploaded videos immediately. In production you may want to
            # restrict this to uploader-only or hide unfinished uploads.
            result = await self.db.query(
                "SELECT *, <-created_by<-user.* AS creator FROM video WHERE status = 'active' OR status = 'processing' OR status = 'queued' ORDER BY created_at DESC LIMIT $limit",
                {"limit": limit}
            )
            if not result:
                logger.info(f"get_for_you_feed: raw result empty for limit={limit}")
                return []
            first = result[0]
            # Handle {'result': [...]}
            if isinstance(first, dict) and 'result' in first:
                res = first.get('result') or []
                # Normalize ids to strings
                for r in res:
                    if isinstance(r, dict) and r.get('id') is not None:
                        try:
                            r['id'] = str(r['id'])
                        except Exception:
                            pass
                    # Ensure a playable URL is present for the frontend
                    if isinstance(r, dict):
                        cdn = r.get('cdn_url') or r.get('playback_url') or r.get('url')
                        if cdn:
                            r.setdefault('cdn_url', cdn)
                            r.setdefault('video_url', cdn)
                logger.info(f"get_for_you_feed: returning {len(res)} records (dict->result)")
                return res
            # Handle [[{...}, {...}]]
            if isinstance(first, list):
                # Normalize list of records
                for r in first:
                    if isinstance(r, dict) and r.get('id') is not None:
                        try:
                            r['id'] = str(r['id'])
                        except Exception:
                            pass
                    if isinstance(r, dict):
                        cdn = r.get('cdn_url') or r.get('playback_url') or r.get('url')
                        if cdn:
                            r.setdefault('cdn_url', cdn)
                            r.setdefault('video_url', cdn)
                logger.info(f"get_for_you_feed: returning {len(first)} records (list)")
                return first
            # If first is a direct record dict, return it wrapped
            if isinstance(first, dict):
                if first.get('id') is not None:
                    try:
                        first['id'] = str(first['id'])
                    except Exception:
                        pass
                cdn = first.get('cdn_url') or first.get('playback_url') or first.get('url')
                if cdn:
                    first.setdefault('cdn_url', cdn)
                    first.setdefault('video_url', cdn)
                logger.info("get_for_you_feed: returning 1 record (single dict)")
                return [first]
            return []
        except Exception as e:
            logger.error(f"Error getting feed: {e}")
            return []

    async def get_following_feed(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get videos from users that the current user follows"""
        try:
            result = await self.db.query(
                """
                SELECT *, <-created_by<-user.* AS creator FROM video
                WHERE status = 'active' AND <-created_by<-user.id IN (
                    SELECT ->follows->user.id FROM $user
                )
                ORDER BY created_at DESC LIMIT $limit
                """,
                {"user": user_id, "limit": limit}
            )
            if not result:
                return []
            first = result[0]
            if isinstance(first, dict) and 'result' in first:
                return first.get('result') or []
            if isinstance(first, list):
                return first
            if isinstance(first, dict):
                return [first]
            return []
        except Exception as e:
            logger.error(f"Error getting following feed: {e}")
            return []

    async def get_trending_feed(self, limit: int = 50) -> List[Dict]:
        """Get trending videos based on view count and engagement"""
        try:
            result = await self.db.query(
                """
                SELECT *, <-created_by<-user.* AS creator FROM video
                WHERE status = 'active'
                ORDER BY view_count DESC, like_count DESC, created_at DESC
                LIMIT $limit
                """,
                {"limit": limit}
            )
            if not result:
                return []
            first = result[0]
            if isinstance(first, dict) and 'result' in first:
                return first.get('result') or []
            if isinstance(first, list):
                return first
            if isinstance(first, dict):
                return [first]
            return []
        except Exception as e:
            logger.error(f"Error getting trending feed: {e}")
            return []

db_client = SurrealDBClient()


# --- Synchronous helpers for worker processes ---
_SYNC_CLIENT = None
_SYNC_CLIENT_LOCK = threading.Lock()

def close_sync_client():
    """Close and clear the cached sync client for this process."""
    global _SYNC_CLIENT
    try:
        with _SYNC_CLIENT_LOCK:
            if _SYNC_CLIENT is not None:
                try:
                    _SYNC_CLIENT.close()
                except Exception:
                    pass
                _SYNC_CLIENT = None
    except Exception:
        pass
def _make_sync_client():
    """Create and return a synchronous Surreal client connected to the
    configured namespace and database. This avoids async event-loop issues
    when used inside Celery worker processes.
    """
    try:
        from surrealdb import Surreal
    except Exception as e:
        logger.error(f"Sync Surreal client unavailable: {e}")
        return None

    global _SYNC_CLIENT
    # Return cached client if available
    try:
        with _SYNC_CLIENT_LOCK:
            if _SYNC_CLIENT is not None:
                return _SYNC_CLIENT
            # Create and cache a new client
            client = Surreal(settings.SURREALDB_URL.replace('ws://', 'http://').replace('wss://', 'https://'))
            # The sync client API may use connect()/signin()/use() differently
            try:
                client.connect()
            except Exception:
                # Some Surreal client versions connect lazily; ignore connect errors
                pass

            try:
                if settings.ENVIRONMENT == 'production':
                    client.signin({
                        'username': settings.SURREALDB_USER,
                        'password': settings.SURREALDB_PASS,
                        'namespace': settings.SURREALDB_NS,
                    })
                else:
                    client.signin({
                        'username': settings.SURREALDB_USER,
                        'password': settings.SURREALDB_PASS,
                    })
            except Exception:
                # signin may be optional locally; ignore
                pass

            try:
                client.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
            except Exception:
                pass

            _SYNC_CLIENT = client
            return _SYNC_CLIENT
    except Exception as e:
        logger.error(f"Failed to create sync Surreal client: {e}")
        return None


def sync_client_get_video(video_id: str) -> Optional[Dict]:
    """Synchronous helper for workers: fetch a video record via the sync
    Surreal client and normalize the result similarly to get_video()."""
    client = _make_sync_client()
    if client is None:
        return None
    try:
        # Query by table + record id using type::thing to be compatible with
        # the sync client's parameter handling across versions.
        if ':' in video_id:
            table, record_id = video_id.split(':', 1)
        else:
            table = 'video'
            record_id = video_id

        # Perform the query and capture any errors; normalize to None on failure
        try:
            res = client.query(
                "SELECT *, <-created_by<-user.* AS creator FROM $table WHERE id = type::thing($table, $record_id)",
                {"table": table, "record_id": record_id}
            )
        except Exception as e:
            logger.debug(f"sync_client_get_video query error, attempting to continue: {e}")
            res = None

        # If no result, attempt a couple of fallbacks and log at INFO so it
        # is visible in Celery worker logs.
        if not res:
            logger.info(f"sync_client_get_video: initial query returned no result for {video_id}, trying fallbacks")
            # Fallback #1: inline type::thing with quoted literals (some sync clients
            # don't accept parameter maps reliably).
            try:
                res = client.query(
                    f"SELECT *, <-created_by<-user.* AS creator FROM {table} WHERE id = type::thing('{table}', '{record_id}')"
                )
            except Exception as e:
                logger.debug(f"sync_client_get_video fallback1 error: {e}")
                res = None

        if not res:
            # Fallback #2: direct id string match (Surreal returns id as 'table:record')
            try:
                res = client.query(
                    f"SELECT *, <-created_by<-user.* AS creator FROM {table} WHERE id = '{table}:{record_id}'"
                )
            except Exception as e:
                logger.debug(f"sync_client_get_video fallback2 error: {e}")
                res = None

        if not res:
            logger.info(f"sync_client_get_video: no result after fallbacks for {video_id}, raw res={res}")
            return None

        first = res[0]
        # Normalize common response shapes
        record = None
        if isinstance(first, dict) and 'result' in first:
            lst = first.get('result') or []
            record = lst[0] if lst else None
        elif isinstance(first, list):
            record = first[0] if first else None
        elif isinstance(first, dict):
            record = first
        else:
            record = None

        # Convert RecordID objects to strings for 'id' field
        if isinstance(record, dict) and record.get('id') is not None:
            try:
                record['id'] = str(record['id'])
            except Exception:
                pass
        return record
    except Exception as e:
        logger.error(f"sync_client_get_video error for {video_id}: {e}")
        return None


def sync_client_update_video_fields(video_id: str, fields: Dict) -> bool:
    """Synchronous helper to update fields on a video via the sync client."""
    client = _make_sync_client()
    if client is None:
        return False
    try:
        params = {}
        set_clauses = []
        for k, v in fields.items():
            params[k] = v
            set_clauses.append(f"{k} = ${k}")
        if not set_clauses:
            return True
        params['id'] = video_id
        set_sql = ", ".join(set_clauses)
        # Attempt 1: parameterized WHERE using $id (preferred)
        try:
            res = client.query(f"UPDATE video SET {set_sql} WHERE id = $id", params)
            # Many sync client versions return the updated record(s) or an
            # empty list when nothing matched. Treat a non-empty response as
            # success.
            if res:
                logger.info(f"sync_client_update_video_fields: parameterized update succeeded for {video_id}")
                return True
        except Exception as e:
            logger.debug(f"sync_client_update_video_fields param update error for {video_id}: {e}")

        # If the parameterized form didn't work (some client versions don't
        # accept RecordID params), try fallbacks that use explicit type::thing
        # or direct id string comparisons. Keep using the same params for SET
        # so complex values (objects) are still passed safely.
        try:
            if ':' in video_id:
                table, record_id = video_id.split(':', 1)
            else:
                table = 'video'
                record_id = video_id

            # Fallback 1: use type::thing inline in WHERE
            try:
                res2 = client.query(
                    f"UPDATE video SET {set_sql} WHERE id = type::thing('{table}', '{record_id}')",
                    params
                )
                if res2:
                    logger.info(f"sync_client_update_video_fields: type::thing fallback succeeded for {video_id}")
                    return True
            except Exception as e:
                logger.debug(f"sync_client_update_video_fields fallback1 error for {video_id}: {e}")

            # Fallback 2: direct id string equality
            try:
                res3 = client.query(
                    f"UPDATE video SET {set_sql} WHERE id = '{table}:{record_id}'",
                    params
                )
                if res3:
                    logger.info(f"sync_client_update_video_fields: id-string fallback succeeded for {video_id}")
                    return True
            except Exception as e:
                logger.debug(f"sync_client_update_video_fields fallback2 error for {video_id}: {e}")

            logger.info(f"sync_client_update_video_fields: no update applied for {video_id} after fallbacks")
            return False
        except Exception as e:
            logger.error(f"sync_client_update_video_fields unexpected error for {video_id}: {e}")
            return False
    except Exception as e:
        logger.error(f"sync_client_update_video_fields error for {video_id}: {e}")
        return False
