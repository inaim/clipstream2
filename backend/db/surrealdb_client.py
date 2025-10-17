from surrealdb import AsyncSurreal
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Union
from utils.config import settings

logger = logging.getLogger(__name__)

class SurrealDBClient:
    def __init__(self):
        self.db: Optional[AsyncSurreal] = None
        self._connected = False
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def connect(self):
        if not self._connected:
            try:
                self.db = AsyncSurreal(settings.SURREALDB_URL)
                await self.db.connect()

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
            result = await self.db.query(
                "SELECT *, <-created_by<-user.* AS creator FROM $video",
                {"video": video_id}
            )
            # The AsyncSurreal client may return different shapes. Normalize safely.
            if not result:
                return None
            first = result[0]
            # If client returns a dict with 'result' key
            if isinstance(first, dict) and 'result' in first:
                res_list = first.get('result') or []
                return res_list[0] if res_list else None
            # If client returns a list whose first element is a list of records
            if isinstance(first, list):
                return first[0] if first else None
            # Fallback: if it's a dict representing the record
            if isinstance(first, dict):
                return first
            return None
        except Exception as e:
            logger.error(f"Error getting video: {e}")
            return None
    
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
            result = await self.db.query(
                "SELECT *, <-created_by<-user.* AS creator FROM video WHERE status = 'active' ORDER BY created_at DESC LIMIT $limit",
                {"limit": limit}
            )
            if not result:
                return []
            first = result[0]
            # Handle {'result': [...]}
            if isinstance(first, dict) and 'result' in first:
                return first.get('result') or []
            # Handle [[{...}, {...}]]
            if isinstance(first, list):
                return first
            # If first is a direct record dict, return it wrapped
            if isinstance(first, dict):
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