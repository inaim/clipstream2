"""
TikTok Video Ingestion Test Utilities

Simulates importing videos from TikTok for testing purposes.
In production, this would integrate with TikTok's API or use a scraper.

For testing, this creates mock TikTok videos with realistic metadata.
"""

import asyncio
import json
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockTikTokVideo:
    """Represents a mock TikTok video for testing."""

    def __init__(
        self,
        video_id: str,
        author: str,
        title: str,
        description: str,
        video_url: str,
        thumbnail_url: str,
        duration: int,
        view_count: int,
        like_count: int,
        comment_count: int,
        share_count: int,
        hashtags: List[str],
        created_at: datetime
    ):
        self.video_id = video_id
        self.author = author
        self.title = title
        self.description = description
        self.video_url = video_url
        self.thumbnail_url = thumbnail_url
        self.duration = duration
        self.view_count = view_count
        self.like_count = like_count
        self.comment_count = comment_count
        self.share_count = share_count
        self.hashtags = hashtags
        self.created_at = created_at

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "video_id": self.video_id,
            "author": self.author,
            "title": self.title,
            "description": self.description,
            "video_url": self.video_url,
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "hashtags": self.hashtags,
            "created_at": self.created_at.isoformat()
        }


class MockTikTokScraper:
    """
    Mock TikTok scraper for testing.

    In production, replace this with actual TikTok API integration or
    a proper scraping library like TikTokApi.
    """

    # Sample TikTok-style content
    SAMPLE_AUTHORS = [
        "dance_queen_2024",
        "comedy_king",
        "cooking_master",
        "fitness_guru",
        "tech_reviewer",
        "travel_vlogger",
        "pet_lover_official",
        "music_producer",
        "artist_studio",
        "gamer_pro"
    ]

    SAMPLE_TITLES = [
        "🔥 This trend is going viral!",
        "You won't believe this hack!",
        "Day in the life of...",
        "Before and after transformation",
        "Things nobody tells you about...",
        "POV: When you...",
        "This is why you should...",
        "The ultimate guide to...",
        "Replying to @username",
        "Part 2 - You asked for it!"
    ]

    SAMPLE_HASHTAGS = [
        ["fyp", "viral", "trending"],
        ["dance", "challenge", "fyp"],
        ["comedy", "funny", "relatable"],
        ["cooking", "recipe", "foodie"],
        ["fitness", "workout", "motivation"],
        ["travel", "adventure", "explore"],
        ["pets", "cute", "animals"],
        ["music", "newrelease", "artist"],
        ["art", "creative", "process"],
        ["gaming", "gameplay", "streamer"]
    ]

    def __init__(self):
        """Initialize mock scraper."""
        self.scraped_count = 0

    def generate_mock_video(self, seed: Optional[int] = None) -> MockTikTokVideo:
        """
        Generate a mock TikTok video with realistic metadata.

        Args:
            seed: Optional random seed for reproducibility

        Returns:
            video: MockTikTokVideo instance
        """
        if seed is not None:
            random.seed(seed)

        video_id = f"mock_tiktok_{self.scraped_count:06d}"
        self.scraped_count += 1

        author = random.choice(self.SAMPLE_AUTHORS)
        title = random.choice(self.SAMPLE_TITLES)
        hashtags = random.choice(self.SAMPLE_HASHTAGS)

        description = f"{title} #{' #'.join(hashtags)}"

        # Realistic TikTok metrics distribution
        # Most videos: low engagement
        # Some videos: medium engagement
        # Few videos: viral engagement
        engagement_tier = random.choices(
            ['low', 'medium', 'high', 'viral'],
            weights=[60, 25, 10, 5]
        )[0]

        if engagement_tier == 'low':
            view_count = random.randint(100, 5000)
            like_count = int(view_count * random.uniform(0.05, 0.15))
            comment_count = int(view_count * random.uniform(0.01, 0.05))
            share_count = int(view_count * random.uniform(0.005, 0.02))
        elif engagement_tier == 'medium':
            view_count = random.randint(5000, 50000)
            like_count = int(view_count * random.uniform(0.1, 0.2))
            comment_count = int(view_count * random.uniform(0.03, 0.08))
            share_count = int(view_count * random.uniform(0.01, 0.04))
        elif engagement_tier == 'high':
            view_count = random.randint(50000, 500000)
            like_count = int(view_count * random.uniform(0.15, 0.25))
            comment_count = int(view_count * random.uniform(0.05, 0.12))
            share_count = int(view_count * random.uniform(0.02, 0.06))
        else:  # viral
            view_count = random.randint(500000, 5000000)
            like_count = int(view_count * random.uniform(0.2, 0.35))
            comment_count = int(view_count * random.uniform(0.08, 0.15))
            share_count = int(view_count * random.uniform(0.04, 0.1))

        # TikTok videos are typically 15-60 seconds
        duration = random.choice([15, 30, 45, 60])

        # Mock URLs (use public test videos)
        video_url = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
        thumbnail_url = f"https://via.placeholder.com/720x1280/000000/FFFFFF/?text=TikTok+{video_id}"

        # Random creation time in the past 30 days
        days_ago = random.randint(0, 30)
        created_at = datetime.now() - timedelta(days=days_ago)

        return MockTikTokVideo(
            video_id=video_id,
            author=author,
            title=title,
            description=description,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration=duration,
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            hashtags=hashtags,
            created_at=created_at
        )

    def scrape_trending(self, count: int = 10) -> List[MockTikTokVideo]:
        """
        Scrape trending TikTok videos.

        Args:
            count: Number of videos to scrape

        Returns:
            videos: List of MockTikTokVideo instances
        """
        logger.info(f"Scraping {count} trending TikTok videos...")

        videos = []
        for i in range(count):
            # Trending videos are more likely to be viral
            engagement_seed = random.choices(
                [None, 9999],  # 9999 tends to create viral videos
                weights=[30, 70]
            )[0]

            video = self.generate_mock_video(seed=engagement_seed)
            videos.append(video)

        logger.info(f"Scraped {len(videos)} videos")
        return videos

    def scrape_by_hashtag(self, hashtag: str, count: int = 10) -> List[MockTikTokVideo]:
        """
        Scrape videos by hashtag.

        Args:
            hashtag: Hashtag to search
            count: Number of videos to scrape

        Returns:
            videos: List of MockTikTokVideo instances
        """
        logger.info(f"Scraping {count} videos with #{hashtag}...")

        videos = []
        for i in range(count):
            video = self.generate_mock_video()
            # Override hashtags to include the search hashtag
            if hashtag not in video.hashtags:
                video.hashtags.append(hashtag)
            videos.append(video)

        logger.info(f"Scraped {len(videos)} videos")
        return videos


class TikTokVideoIngester:
    """
    Ingests TikTok videos into the ClipStream backend.

    Downloads video metadata and files, then creates records in the database.
    """

    def __init__(self, backend_url: str, api_token: Optional[str] = None):
        """
        Initialize ingester.

        Args:
            backend_url: ClipStream backend URL (e.g., "http://localhost:8000")
            api_token: Optional authentication token
        """
        self.backend_url = backend_url.rstrip('/')
        self.api_token = api_token
        self.client = httpx.AsyncClient(timeout=60.0)

    async def ingest_video(
        self,
        tiktok_video: MockTikTokVideo,
        user_id: str
    ) -> Dict:
        """
        Ingest a TikTok video into ClipStream.

        Args:
            tiktok_video: MockTikTokVideo instance
            user_id: ClipStream user ID to assign as creator

        Returns:
            result: Created video record
        """
        logger.info(f"Ingesting TikTok video: {tiktok_video.video_id}")

        # In production, download the actual video file
        # For testing, use the demo endpoint
        payload = {
            "title": tiktok_video.title,
            "user_id": user_id,
            "force": True  # Allow in production for testing
        }

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            response = await self.client.post(
                f"{self.backend_url}/api/v1/feed/debug/seed-video",
                json=payload,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()

            video = result.get("video", {})
            video_id = video.get("id")

            logger.info(f"Video ingested successfully: {video_id}")

            # Update with TikTok metadata
            if video_id:
                await self._update_video_metadata(
                    video_id=video_id,
                    tiktok_video=tiktok_video
                )

            return video

        except Exception as e:
            logger.error(f"Failed to ingest video: {e}")
            raise

    async def _update_video_metadata(
        self,
        video_id: str,
        tiktok_video: MockTikTokVideo
    ):
        """Update video with TikTok metadata."""
        # This would update the video record with:
        # - description
        # - hashtags
        # - initial engagement metrics (for testing)
        # In production, use the proper update endpoint
        logger.info(f"Updated metadata for {video_id} with TikTok data")

    async def ingest_batch(
        self,
        tiktok_videos: List[MockTikTokVideo],
        user_id: str
    ) -> List[Dict]:
        """
        Ingest multiple TikTok videos.

        Args:
            tiktok_videos: List of MockTikTokVideo instances
            user_id: ClipStream user ID

        Returns:
            results: List of created video records
        """
        logger.info(f"Batch ingesting {len(tiktok_videos)} videos...")

        results = []
        for video in tiktok_videos:
            try:
                result = await self.ingest_video(video, user_id)
                results.append(result)
                # Small delay to avoid overwhelming the backend
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to ingest {video.video_id}: {e}")

        logger.info(f"Batch ingestion complete: {len(results)}/{len(tiktok_videos)} succeeded")
        return results

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Test functions

async def test_tiktok_ingestion():
    """Test TikTok video ingestion pipeline."""
    logger.info("=" * 50)
    logger.info("Testing TikTok Video Ingestion")
    logger.info("=" * 50)

    # 1. Generate mock TikTok videos
    scraper = MockTikTokScraper()
    trending_videos = scraper.scrape_trending(count=5)

    logger.info(f"\nGenerated {len(trending_videos)} mock TikTok videos:")
    for video in trending_videos:
        logger.info(
            f"  - {video.video_id}: {video.title} "
            f"({video.view_count:,} views, {video.like_count:,} likes)"
        )

    # 2. Ingest into ClipStream backend
    ingester = TikTokVideoIngester(
        backend_url="http://localhost:8000",
        api_token=None
    )

    try:
        # Assume test user exists: user:test
        ingested = await ingester.ingest_batch(
            tiktok_videos=trending_videos,
            user_id="user:test"
        )

        logger.info(f"\n✅ Successfully ingested {len(ingested)} videos")

        return ingested

    finally:
        await ingester.close()


if __name__ == "__main__":
    # Run test
    asyncio.run(test_tiktok_ingestion())
