"""
TikTok Auto-Ingestion Service

Continuously fetches trending TikTok videos and ingests them into the platform.

Features:
- Background worker that runs every N minutes
- Fetches trending TikTok videos
- Downloads them with yt-dlp
- Ingests into SurrealDB automatically
- Configurable fetch interval
- Start/stop controls via API
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from app.tiktok_scraper import TikTokScraper
from db.client import get_db

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

# How often to fetch new TikTok videos (seconds)
FETCH_INTERVAL = 300  # 5 minutes

# How many videos to fetch per interval
VIDEOS_PER_FETCH = 10

# Download directory
DOWNLOAD_DIR = "/tmp/tiktok_auto_ingest"

# TikTok trending hashtags to scrape
TRENDING_HASHTAGS = [
    "fyp", "foryou", "viral", "trending",
    "funny", "comedy", "sports", "music",
    "gaming", "dance", "cooking", "travel"
]


# ============================================================================
# AUTO-INGESTION SERVICE
# ============================================================================

class TikTokAutoIngestion:
    """
    Background service for automatic TikTok video ingestion.

    Usage:
        service = TikTokAutoIngestion()
        await service.start()  # Runs in background
        await service.stop()   # Stop ingestion
    """

    def __init__(
        self,
        fetch_interval: int = FETCH_INTERVAL,
        videos_per_fetch: int = VIDEOS_PER_FETCH,
        download_dir: str = DOWNLOAD_DIR
    ):
        """
        Initialize auto-ingestion service.

        Args:
            fetch_interval: Seconds between fetches (default: 300 = 5 minutes)
            videos_per_fetch: Videos to fetch per interval (default: 10)
            download_dir: Directory to store downloaded videos
        """
        self.fetch_interval = fetch_interval
        self.videos_per_fetch = videos_per_fetch
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.scraper = TikTokScraper(download_dir=str(self.download_dir))
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

        # Stats
        self.total_fetched = 0
        self.total_ingested = 0
        self.total_failed = 0
        self.last_fetch_time = None

    async def start(self):
        """Start the auto-ingestion service."""
        if self.is_running:
            logger.warning("Auto-ingestion already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run())
        logger.info(f"Started TikTok auto-ingestion (interval: {self.fetch_interval}s)")

    async def stop(self):
        """Stop the auto-ingestion service."""
        if not self.is_running:
            logger.warning("Auto-ingestion not running")
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped TikTok auto-ingestion")

    async def _run(self):
        """Main loop for auto-ingestion."""
        logger.info("TikTok auto-ingestion worker started")

        while self.is_running:
            try:
                # Fetch and ingest videos
                await self._fetch_and_ingest()

                # Update last fetch time
                self.last_fetch_time = time.time()

                # Wait for next interval
                logger.info(f"Waiting {self.fetch_interval}s until next fetch...")
                await asyncio.sleep(self.fetch_interval)

            except asyncio.CancelledError:
                logger.info("Auto-ingestion cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-ingestion loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)

    async def _fetch_and_ingest(self):
        """Fetch trending TikTok videos and ingest them."""
        logger.info(f"Fetching {self.videos_per_fetch} trending TikTok videos...")

        # Get trending TikTok URLs
        # Note: This requires TikTok API access or web scraping
        # For now, we'll use a placeholder that demonstrates the flow

        tiktok_urls = await self._get_trending_tiktok_urls()

        if not tiktok_urls:
            logger.warning("No TikTok URLs found")
            return

        logger.info(f"Found {len(tiktok_urls)} TikTok URLs to process")

        # Download and ingest each video
        ingested_count = 0
        failed_count = 0

        for url_data in tiktok_urls:
            try:
                # Download video
                video_info = await self.scraper.download_video(url_data["url"])

                if not video_info:
                    logger.warning(f"Failed to download: {url_data['url']}")
                    failed_count += 1
                    continue

                # Ingest into database
                success = await self._ingest_video(video_info, url_data.get("category", "general"))

                if success:
                    ingested_count += 1
                    logger.info(f"Ingested: {video_info.get('title', 'Unknown')}")
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing {url_data['url']}: {e}")
                failed_count += 1

        # Update stats
        self.total_fetched += len(tiktok_urls)
        self.total_ingested += ingested_count
        self.total_failed += failed_count

        logger.info(f"Batch complete: {ingested_count} ingested, {failed_count} failed")

    async def _get_trending_tiktok_urls(self) -> List[Dict[str, Any]]:
        """
        Get trending TikTok video URLs.

        This is a placeholder. In production, you would:
        1. Use TikTok API (requires API key)
        2. Scrape TikTok trending page (requires web scraping)
        3. Use a TikTok data provider service

        Returns:
            List of dicts with 'url' and 'category'
        """
        # PLACEHOLDER: Return empty list
        # In production, implement one of these:

        # Option 1: TikTok API (requires approval)
        # from TikTokApi import TikTokApi
        # async with TikTokApi() as api:
        #     trending = api.trending.videos(count=self.videos_per_fetch)
        #     return [{"url": v.video.downloadAddr, "category": "trending"} for v in trending]

        # Option 2: Web scraping (may violate TOS)
        # urls = await scrape_tiktok_trending_page()
        # return urls

        # Option 3: Manual URL list (for testing)
        # Read from a file with TikTok URLs
        url_file = self.download_dir / "tiktok_urls.txt"
        if url_file.exists():
            urls = []
            with open(url_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        urls.append({
                            "url": parts[0],
                            "category": parts[1] if len(parts) > 1 else "general"
                        })
            return urls[:self.videos_per_fetch]

        logger.warning("No TikTok URL source configured. See documentation.")
        return []

    async def _ingest_video(self, video_info: Dict[str, Any], category: str) -> bool:
        """
        Ingest a downloaded video into the database.

        Args:
            video_info: Video metadata from scraper
            category: Video category

        Returns:
            True if ingested successfully
        """
        try:
            db = await get_db()

            # Create video record
            video_data = {
                "url": video_info.get("video_path", ""),
                "title": video_info.get("title", "Unknown"),
                "category": category,
                "duration": video_info.get("duration", 0),
                "creator_id": f"tiktok:{video_info.get('creator', 'unknown')}",
                "tags": video_info.get("hashtags", []),
                "view_count": video_info.get("view_count", 0),
                "like_count": video_info.get("like_count", 0),
                "comment_count": video_info.get("comment_count", 0),
                "share_count": video_info.get("share_count", 0),
                "description": video_info.get("description", ""),
                "thumbnail": video_info.get("thumbnail", ""),
                "upload_date": video_info.get("upload_date", ""),
                "source": "tiktok",
                "auto_ingested": True,
                "ingested_at": time.time()
            }

            # Insert into database
            result = await db.create("video", video_data)

            if result:
                logger.debug(f"Ingested video: {result[0]['id']}")
                return True
            else:
                logger.error("Failed to insert video into database")
                return False

        except Exception as e:
            logger.error(f"Error ingesting video: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        return {
            "is_running": self.is_running,
            "fetch_interval": self.fetch_interval,
            "videos_per_fetch": self.videos_per_fetch,
            "total_fetched": self.total_fetched,
            "total_ingested": self.total_ingested,
            "total_failed": self.total_failed,
            "success_rate": (
                self.total_ingested / self.total_fetched
                if self.total_fetched > 0 else 0
            ),
            "last_fetch_time": self.last_fetch_time
        }


# ============================================================================
# GLOBAL SERVICE INSTANCE
# ============================================================================

_auto_ingestion_service: Optional[TikTokAutoIngestion] = None


async def get_auto_ingestion_service() -> TikTokAutoIngestion:
    """Get global auto-ingestion service instance."""
    global _auto_ingestion_service

    if _auto_ingestion_service is None:
        _auto_ingestion_service = TikTokAutoIngestion()

    return _auto_ingestion_service


async def start_auto_ingestion():
    """Start the auto-ingestion service."""
    service = await get_auto_ingestion_service()
    await service.start()


async def stop_auto_ingestion():
    """Stop the auto-ingestion service."""
    service = await get_auto_ingestion_service()
    await service.stop()


async def get_ingestion_stats() -> Dict[str, Any]:
    """Get auto-ingestion statistics."""
    service = await get_auto_ingestion_service()
    return service.get_stats()
