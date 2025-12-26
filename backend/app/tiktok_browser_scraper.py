"""
TikTok Browser-Based Scraper

Uses Playwright headless browser to scrape TikTok feeds in real-time.
Supports infinite scrolling to continuously pull new video content.

Features:
- Headless browser automation with Playwright
- Infinite scroll support for continuous feed scraping
- Video URL and metadata extraction from DOM
- Real-time feed scraping (trending, hashtags, user profiles)
- Anti-detection measures (user agent, viewport, etc.)
- Concurrent video processing
"""

import asyncio
import logging
import json
import re
import random
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

# Realistic user agents for rotation
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Viewport sizes for randomization
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 2560, 'height': 1440},
]


class TikTokBrowserScraper:
    """
    Headless browser scraper for TikTok video feeds.

    Uses Playwright to navigate TikTok and extract video URLs through infinite scrolling.
    """

    def __init__(
        self,
        headless: bool = True,
        max_videos: int = 50,
        scroll_delay: float = 2.0,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        rotate_agents: bool = True
    ):
        """
        Initialize TikTok browser scraper.

        Args:
            headless: Run browser in headless mode
            max_videos: Maximum videos to scrape per session
            scroll_delay: Delay between scrolls (seconds)
            user_agent: Custom user agent string (if None, will rotate)
            proxy: Proxy server URL (e.g., "http://proxy-server:port")
            rotate_agents: Whether to rotate user agents on each request
        """
        self.headless = headless
        self.max_videos = max_videos
        self.scroll_delay = scroll_delay
        self.proxy = proxy
        self.rotate_agents = rotate_agents

        # User agent handling
        if user_agent:
            self.user_agent = user_agent
            self.rotate_agents = False  # Don't rotate if custom UA provided
        else:
            self.user_agent = random.choice(USER_AGENTS) if rotate_agents else USER_AGENTS[0]

        self.browser: Optional[Browser] = None
        self.playwright = None

        # Track seen videos to avoid duplicates
        self.seen_video_ids: Set[str] = set()

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser instance."""
        if self.browser:
            logger.warning("Browser already started")
            return

        logger.info("Starting Playwright browser...")
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy}")

        self.playwright = await async_playwright().start()

        # Browser launch arguments for anti-detection
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]

        # Build launch options
        launch_options = {
            'headless': self.headless,
            'args': browser_args
        }

        # Add proxy if provided
        if self.proxy:
            launch_options['proxy'] = {
                'server': self.proxy
            }

        # Launch browser with anti-detection settings
        self.browser = await self.playwright.chromium.launch(**launch_options)

        logger.info("Browser started successfully")

    async def close(self):
        """Close the browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("Browser closed")

    async def create_page(self) -> Page:
        """
        Create a new page with anti-detection settings.

        Returns:
            Configured Playwright page
        """
        if not self.browser:
            await self.start()

        context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
        )

        page = await context.new_page()

        # Inject anti-detection scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        return page

    async def scrape_trending_feed(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape TikTok trending feed.

        Args:
            limit: Maximum number of videos to scrape (uses max_videos if None)

        Returns:
            List of video metadata dicts
        """
        max_vids = limit or self.max_videos
        url = "https://www.tiktok.com/foryou"

        logger.info(f"Scraping TikTok trending feed (limit: {max_vids})")
        return await self._scrape_feed(url, max_vids, feed_type="trending")

    async def scrape_hashtag_feed(self, hashtag: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape videos from a specific hashtag.

        Args:
            hashtag: Hashtag to scrape (without #)
            limit: Maximum number of videos to scrape

        Returns:
            List of video metadata dicts
        """
        max_vids = limit or self.max_videos
        hashtag = hashtag.lstrip('#')
        url = f"https://www.tiktok.com/tag/{hashtag}"

        logger.info(f"Scraping TikTok hashtag #{hashtag} (limit: {max_vids})")
        return await self._scrape_feed(url, max_vids, feed_type="hashtag", category=hashtag)

    async def scrape_user_videos(self, username: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape videos from a specific user profile.

        Args:
            username: TikTok username (without @)
            limit: Maximum number of videos to scrape

        Returns:
            List of video metadata dicts
        """
        max_vids = limit or self.max_videos
        username = username.lstrip('@')
        url = f"https://www.tiktok.com/@{username}"

        logger.info(f"Scraping TikTok user @{username} (limit: {max_vids})")
        return await self._scrape_feed(url, max_vids, feed_type="user", creator=username)

    async def _scrape_feed(
        self,
        url: str,
        max_videos: int,
        feed_type: str = "general",
        **metadata_overrides
    ) -> List[Dict[str, Any]]:
        """
        Generic feed scraping with infinite scroll.

        Args:
            url: TikTok URL to scrape
            max_videos: Maximum videos to collect
            feed_type: Type of feed being scraped
            **metadata_overrides: Additional metadata to add to each video

        Returns:
            List of video metadata dicts
        """
        page = await self.create_page()
        videos = []

        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait for initial content to load
            await asyncio.sleep(3)

            # Scroll and collect videos
            consecutive_no_new = 0
            max_consecutive = 5

            while len(videos) < max_videos and consecutive_no_new < max_consecutive:
                # Extract video elements from current viewport
                new_videos = await self._extract_videos_from_page(page, feed_type, **metadata_overrides)

                if new_videos:
                    videos.extend(new_videos)
                    consecutive_no_new = 0
                    logger.info(f"Found {len(new_videos)} new videos (total: {len(videos)}/{max_videos})")
                else:
                    consecutive_no_new += 1
                    logger.debug(f"No new videos found ({consecutive_no_new}/{max_consecutive})")

                # Stop if we've reached the limit
                if len(videos) >= max_videos:
                    break

                # Scroll down to load more videos
                await self._scroll_down(page)
                await asyncio.sleep(self.scroll_delay)

            # Trim to exact limit
            videos = videos[:max_videos]

            logger.info(f"Scraping complete: collected {len(videos)} videos")
            return videos

        except PlaywrightTimeout:
            logger.error(f"Timeout loading {url}")
            return videos
        except Exception as e:
            logger.error(f"Error scraping feed: {e}")
            return videos
        finally:
            await page.close()

    async def _extract_videos_from_page(
        self,
        page: Page,
        feed_type: str,
        **metadata_overrides
    ) -> List[Dict[str, Any]]:
        """
        Extract video data from current page state.

        Args:
            page: Playwright page
            feed_type: Type of feed
            **metadata_overrides: Additional metadata

        Returns:
            List of new video metadata dicts
        """
        videos = []

        try:
            # TikTok video containers typically use data-e2e="recommend-list-item-container"
            # or similar selectors. We'll use multiple strategies.

            # Strategy 1: Find video links
            video_links = await page.locator('a[href*="/video/"]').all()

            for link in video_links:
                try:
                    href = await link.get_attribute('href')
                    if not href or '/video/' not in href:
                        continue

                    # Extract video ID from URL
                    video_id = self._extract_video_id(href)
                    if not video_id or video_id in self.seen_video_ids:
                        continue

                    self.seen_video_ids.add(video_id)

                    # Try to extract metadata from parent container
                    container = link.locator('xpath=ancestor::div[contains(@class, "DivItemContainer")]').first

                    # Extract visible metadata
                    metadata = await self._extract_video_metadata(page, link, container)

                    # Build video data
                    video_data = {
                        'url': href if href.startswith('http') else f"https://www.tiktok.com{href}",
                        'video_id': video_id,
                        'feed_type': feed_type,
                        'scraped_at': datetime.utcnow().isoformat(),
                        **metadata,
                        **metadata_overrides
                    }

                    videos.append(video_data)
                    logger.debug(f"Extracted video: {video_id}")

                except Exception as e:
                    logger.debug(f"Error extracting video from link: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting videos from page: {e}")

        return videos

    async def _extract_video_metadata(
        self,
        page: Page,
        link_element,
        container_element
    ) -> Dict[str, Any]:
        """
        Extract metadata from video element.

        Args:
            page: Playwright page
            link_element: Video link element
            container_element: Parent container element

        Returns:
            Metadata dict
        """
        metadata = {}

        try:
            # Try to extract description/title
            try:
                desc_elem = await container_element.locator('[data-e2e="browse-video-desc"]').first.text_content()
                metadata['description'] = desc_elem.strip() if desc_elem else ""
            except:
                pass

            # Try to extract creator username
            try:
                creator_elem = await container_element.locator('[data-e2e="browse-username"]').first.text_content()
                metadata['creator'] = creator_elem.strip().lstrip('@') if creator_elem else ""
            except:
                pass

            # Try to extract view count, likes, etc.
            try:
                stats_elem = await container_element.locator('[data-e2e="like-count"]').first.text_content()
                metadata['like_count'] = self._parse_count(stats_elem)
            except:
                pass

            try:
                views_elem = await container_element.locator('[data-e2e="video-views"]').first.text_content()
                metadata['view_count'] = self._parse_count(views_elem)
            except:
                pass

            # Extract hashtags from description
            if 'description' in metadata:
                hashtags = re.findall(r'#(\w+)', metadata['description'])
                metadata['hashtags'] = hashtags

                # Use first hashtag as category if not set
                if hashtags and 'category' not in metadata:
                    metadata['category'] = hashtags[0].lower()

        except Exception as e:
            logger.debug(f"Error extracting metadata: {e}")

        return metadata

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from TikTok URL.

        Args:
            url: TikTok video URL

        Returns:
            Video ID or None
        """
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None

    def _parse_count(self, text: str) -> int:
        """
        Parse TikTok count strings (e.g., "1.2M", "45.6K").

        Args:
            text: Count text

        Returns:
            Integer count
        """
        if not text:
            return 0

        text = text.strip().upper()

        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000,
        }

        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    number = float(text.replace(suffix, '').strip())
                    return int(number * multiplier)
                except ValueError:
                    return 0

        try:
            return int(text)
        except ValueError:
            return 0

    async def _scroll_down(self, page: Page):
        """
        Scroll down the page to trigger infinite scroll.

        Args:
            page: Playwright page
        """
        await page.evaluate('window.scrollBy(0, window.innerHeight)')

    async def scrape_multiple_hashtags(
        self,
        hashtags: List[str],
        videos_per_hashtag: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scrape videos from multiple hashtags concurrently.

        Args:
            hashtags: List of hashtags to scrape
            videos_per_hashtag: Videos to scrape per hashtag

        Returns:
            Combined list of video metadata
        """
        logger.info(f"Scraping {len(hashtags)} hashtags concurrently")

        tasks = [
            self.scrape_hashtag_feed(hashtag, videos_per_hashtag)
            for hashtag in hashtags
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_videos = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Hashtag scraping failed: {result}")
            elif isinstance(result, list):
                all_videos.extend(result)

        logger.info(f"Scraped {len(all_videos)} total videos from hashtags")
        return all_videos


# Convenience functions
async def scrape_tiktok_trending(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Scrape TikTok trending feed.

    Args:
        limit: Maximum videos to scrape

    Returns:
        List of video metadata dicts
    """
    async with TikTokBrowserScraper(max_videos=limit) as scraper:
        return await scraper.scrape_trending_feed(limit)


async def scrape_tiktok_hashtags(
    hashtags: List[str],
    videos_per_hashtag: int = 10
) -> List[Dict[str, Any]]:
    """
    Scrape multiple TikTok hashtags.

    Args:
        hashtags: List of hashtags
        videos_per_hashtag: Videos per hashtag

    Returns:
        List of video metadata dicts
    """
    async with TikTokBrowserScraper() as scraper:
        return await scraper.scrape_multiple_hashtags(hashtags, videos_per_hashtag)


# Example usage
async def main():
    """Example: Scrape TikTok feeds with browser automation."""

    # Example 1: Scrape trending feed
    logger.info("=== Scraping Trending Feed ===")
    trending_videos = await scrape_tiktok_trending(limit=20)
    print(f"Found {len(trending_videos)} trending videos")
    for video in trending_videos[:5]:
        print(f"  - {video.get('description', 'No description')[:50]}... ({video['url']})")

    # Example 2: Scrape multiple hashtags
    logger.info("\n=== Scraping Hashtags ===")
    hashtags = ['fyp', 'viral', 'funny', 'cooking']
    hashtag_videos = await scrape_tiktok_hashtags(hashtags, videos_per_hashtag=5)
    print(f"Found {len(hashtag_videos)} videos from hashtags")

    # Example 3: Scrape specific user
    logger.info("\n=== Scraping User Profile ===")
    async with TikTokBrowserScraper() as scraper:
        user_videos = await scraper.scrape_user_videos('username', limit=10)
        print(f"Found {len(user_videos)} videos from user")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
