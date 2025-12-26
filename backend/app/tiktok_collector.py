"""
Headless TikTok URL collector.

Uses Playwright to open the Explore page, listens for API responses to extract
aweme IDs, and returns full TikTok video URLs. This is a best-effort helper
for auto-ingestion when no manual URL list is provided.
"""

import asyncio
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


async def collect_tiktok_explore_urls(max_urls: int = 20, scroll_steps: int = 30) -> List[str]:
    """
    Collect TikTok video URLs from the Explore page using headless Chromium.

    Returns:
        List of full TikTok video URLs (e.g., https://www.tiktok.com/@user/video/123...)
    """
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        logger.warning(f"Playwright not available for TikTok collection: {e}")
        return []

    collected: Set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_response(response):
            if "api" not in response.url or len(collected) >= max_urls:
                return
            try:
                data = await response.json()
            except Exception:
                return

            for aweme in data.get("aweme_list", []) or []:
                try:
                    video_id = aweme["aweme_id"]
                    username = aweme["author"]["unique_id"]
                    url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                    collected.add(url)
                    if len(collected) >= max_urls:
                        break
                except Exception:
                    continue

        page.on("response", lambda resp: asyncio.create_task(handle_response(resp)))
        await page.goto("https://www.tiktok.com/explore", wait_until="networkidle")

        for _ in range(scroll_steps):
            if len(collected) >= max_urls:
                break
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await asyncio.sleep(1.25)

        await browser.close()

    urls = list(collected)[:max_urls]
    logger.info(f"Collected {len(urls)} TikTok URLs from Explore via Playwright")
    return urls
