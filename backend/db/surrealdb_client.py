from surrealdb import Surreal
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict
from utils.config import settings

logger = logging.getLogger(__name__)

class SurrealDBClient:
    def __init__(self):
        self.db = None
        self._connected = False
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def connect(self):
        if not self._connected:
            try:
                # Run sync operation in thread pool
                loop = asyncio.get_event_loop()
                
                def _connect():
                    db = Surreal(settings.SURREALDB_URL)
                    db.signin({
                        "username": settings.SURREALDB_USER,
                        "password": settings.SURREALDB_PASS
                    })
                    db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
                    return db
                
                self.db = await loop.run_in_executor(self.executor, _connect)
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
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.db.create("user", {
                "email": email,
                "password_hash": password_hash,
                "display_name": display_name or email.split("@")[0],
                "watch_tokens": 0,
                "watch_tokens_pending": 0
            })
        )
        # SurrealDB create returns the created record directly
        return result if result else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.db.query(
                "SELECT * FROM user WHERE email = $email LIMIT 1",
                {"email": email}
            )
        )
        return result[0]['result'][0] if result and result[0]['result'] else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, lambda: self.db.select(user_id))
    
    async def create_video(self, user_id: str, title: str, cdn_url: str, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        
        def _create_video():
            video = self.db.create("video", {
                "title": title,
                "cdn_url": cdn_url,
                "status": "active",
                **kwargs
            })
            self.db.query(
                "RELATE $user->created_by->$video",
                {"user": user_id, "video": video[0]['id']}
            )
            return video[0]
        
        return await loop.run_in_executor(self.executor, _create_video)
    
    async def get_video(self, video_id: str) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.db.query(
                "SELECT *, <-created_by<-user.* AS creator FROM $video",
                {"video": video_id}
            )
        )
        return result[0]['result'][0] if result and result[0]['result'] else None
    
    async def earn_tokens(self, user_id: str, amount: int, reason: str, video_id: str = None) -> Dict:
        loop = asyncio.get_event_loop()
        
        def _earn():
            earning = self.db.create("earning", {
                "creator": user_id,
                "amount": amount,
                "reason": reason,
                "video": video_id,
                "settled_on_chain": False
            })
            self.db.query(
                "UPDATE $user SET watch_tokens_pending += $amount",
                {"user": user_id, "amount": amount}
            )
            # SurrealDB create returns the created record directly
            return earning
        
        return await loop.run_in_executor(self.executor, _earn)
    
    async def get_for_you_feed(self, limit: int = 50) -> List[Dict]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.db.query(
                "SELECT *, <-created_by<-user.* AS creator FROM video WHERE status = 'active' ORDER BY created_at DESC LIMIT $limit",
                {"limit": limit}
            )
        )
        return result[0]['result'] if result and result[0]['result'] else []

db_client = SurrealDBClient()