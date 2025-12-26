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
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path
import shutil
import hashlib
import os

from app.tiktok_scraper import TikTokScraper
from app.tiktok_browser_scraper import TikTokBrowserScraper, scrape_tiktok_hashtags
from db.surrealdb_client import db_client
from utils.config import settings

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
        download_dir: str = DOWNLOAD_DIR,
        use_browser: bool = True
    ):
        """
        Initialize auto-ingestion service.

        Args:
            fetch_interval: Seconds between fetches (default: 300 = 5 minutes)
            videos_per_fetch: Videos to fetch per interval (default: 10)
            download_dir: Directory to store downloaded videos
            use_browser: Use browser scraping for feed discovery (default: True)
        """
        self.fetch_interval = fetch_interval
        self.videos_per_fetch = videos_per_fetch
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.use_browser = use_browser

        self.scraper = TikTokScraper(download_dir=str(self.download_dir))
        self.browser_scraper: Optional[TikTokBrowserScraper] = None
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

        # Initialize browser scraper if enabled
        if self.use_browser:
            self.browser_scraper = TikTokBrowserScraper(max_videos=self.videos_per_fetch)
            await self.browser_scraper.start()
            logger.info("Browser scraper initialized")

        self.is_running = True
        self.task = asyncio.create_task(self._run())
        logger.info(f"Started TikTok auto-ingestion (interval: {self.fetch_interval}s, browser: {self.use_browser})")

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

        # Close browser scraper if active
        if self.browser_scraper:
            await self.browser_scraper.close()
            self.browser_scraper = None
            logger.info("Browser scraper closed")

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

                # Merge browser-scraped metadata if available
                if "metadata" in url_data:
                    browser_metadata = url_data["metadata"]
                    # Prefer browser metadata for fields that might be more accurate
                    video_info.setdefault("description", browser_metadata.get("description", ""))
                    video_info.setdefault("creator", browser_metadata.get("creator", ""))
                    video_info.setdefault("hashtags", browser_metadata.get("hashtags", []))
                    if "view_count" in browser_metadata:
                        video_info["view_count"] = browser_metadata["view_count"]
                    if "like_count" in browser_metadata:
                        video_info["like_count"] = browser_metadata["like_count"]

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

        Uses browser scraping if enabled, otherwise falls back to manual URL list.

        Returns:
            List of dicts with 'url' and 'category'
        """
        # Option 1: Browser scraping (if enabled)
        if self.use_browser and self.browser_scraper:
            try:
                logger.info("Using browser scraper to fetch trending videos")

                # Scrape from multiple hashtags for diversity
                videos = await self.browser_scraper.scrape_multiple_hashtags(
                    TRENDING_HASHTAGS,
                    videos_per_hashtag=max(2, self.videos_per_fetch // len(TRENDING_HASHTAGS))
                )

                if videos:
                    # Convert to expected format
                    url_list = []
                    for video in videos[:self.videos_per_fetch]:
                        url_list.append({
                            "url": video["url"],
                            "category": video.get("category", "general"),
                            "metadata": video  # Pass full scraped metadata
                        })

                    logger.info(f"Browser scraper found {len(url_list)} videos")
                    return url_list
                else:
                    logger.warning("Browser scraper returned no videos, falling back to manual list")

            except Exception as e:
                logger.error(f"Browser scraping failed: {e}, falling back to manual list")

        # Option 2: Manual URL list (fallback for testing)
        url_file = Path(__file__).resolve().parent / "tiktok_urls.txt"
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

            if urls:
                logger.info(f"Using manual URL list: {len(urls)} videos")
                return urls[:self.videos_per_fetch]

        logger.warning("No TikTok URL source available. Configure browser scraping or add tiktok_urls.txt")
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
            video_path = Path(video_info.get("video_path", ""))
            if not video_path.exists():
                logger.error(f"Video file missing: {video_path}")
                return False

            dest_path, cdn_url = self._store_in_uploads(video_path)

            # Compute hash if missing
            content_hash = video_info.get("content_hash")
            if not content_hash:
                content_hash = self._compute_hash(dest_path)

            created = await db_client.create_video(
                user_id="user:tiktok_auto",
                title=video_info.get("title", "TikTok Video"),
                cdn_url=cdn_url,
                filename=dest_path.name,
                content_hash=content_hash,
                file_size=dest_path.stat().st_size,
                status="active",
                description=video_info.get("description", ""),
                tags=video_info.get("hashtags", []),
                category=category,
                source="tiktok",
                auto_ingested=True,
                source_metadata={
                    "creator": video_info.get("creator"),
                    "creator_name": video_info.get("creator_name"),
                    "view_count": video_info.get("view_count"),
                    "like_count": video_info.get("like_count"),
                    "comment_count": video_info.get("comment_count"),
                    "share_count": video_info.get("share_count"),
                    "upload_date": video_info.get("upload_date"),
                }
            )

            if created:
                logger.info(f"Ingested video {created.get('id')} ({dest_path.name})")
                return True

            logger.error("Failed to insert video into database")
            return False

        except Exception as e:
            logger.error(f"Error ingesting video: {e}")
            return False

    def _store_in_uploads(self, source: Path) -> (Path, str):
        """Copy the downloaded video into the uploads directory and return (path, cdn_url)."""
        uploads_dir = Path(settings.UPLOAD_DIR)
        uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = source.suffix or ".mp4"
        dest_name = f"tiktok_{uuid.uuid4().hex}{ext}"
        dest_path = uploads_dir / dest_name
        shutil.copy(source, dest_path)
        cdn_url = f"/uploads/{dest_name}"
        return dest_path, cdn_url

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash for a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        return {
            "is_running": self.is_running,
            "fetch_interval": self.fetch_interval,
            "videos_per_fetch": self.videos_per_fetch,
            "use_browser": self.use_browser,
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
