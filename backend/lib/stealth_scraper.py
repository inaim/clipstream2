"""
Stealth Scraper Library - Universal Anti-Detection Module

A reusable library for bypassing bot detection on websites.
Can be used across multiple projects for web scraping with anti-detection features.

Features:
- User agent rotation (20+ realistic fingerprints)
- Proxy rotation and management
- Browser fingerprinting evasion
- Randomized human-like behavior
- IP hiding and rotation
- Request rate limiting
- Session management
- Cookies and headers management

Usage:
    from lib.stealth_scraper import StealthScraper, ProxyRotator

    # Basic usage
    scraper = StealthScraper()
    async with scraper.create_session() as session:
        data = await scraper.fetch(session, "https://example.com")

    # With proxy rotation
    proxy_rotator = ProxyRotator(proxies=["http://proxy1:port", "http://proxy2:port"])
    scraper = StealthScraper(proxy_rotator=proxy_rotator)
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


# ============================================================================
# USER AGENTS DATABASE
# ============================================================================

USER_AGENTS = [
    # Chrome on Windows (Latest versions)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",

    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",

    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",

    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",

    # Mobile Chrome (Android)
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.71 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",

    # Mobile Safari (iOS)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

# Viewport configurations
VIEWPORTS = [
    {'width': 1920, 'height': 1080},   # Full HD
    {'width': 1366, 'height': 768},    # Common laptop
    {'width': 1536, 'height': 864},    # HD+
    {'width': 1440, 'height': 900},    # MacBook Pro 13"
    {'width': 2560, 'height': 1440},   # QHD
    {'width': 1280, 'height': 720},    # HD
    {'width': 1600, 'height': 900},    # HD+
]

# Timezone options
TIMEZONES = [
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
]

# Locale options
LOCALES = [
    'en-US',
    'en-GB',
    'en-CA',
]


# ============================================================================
# PROXY MANAGEMENT
# ============================================================================

@dataclass
class ProxyInfo:
    """Information about a proxy server."""
    url: str
    last_used: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    avg_response_time: float = 0.0
    is_working: bool = True


class ProxyRotator:
    """
    Manages a pool of proxies with rotation and health tracking.

    Features:
    - Round-robin rotation
    - Health monitoring
    - Automatic failover
    - Performance tracking

    Usage:
        proxies = [
            "http://proxy1.example.com:8080",
            "http://user:pass@proxy2.example.com:3128",
            "http://proxy3.example.com:8888",
        ]
        rotator = ProxyRotator(proxies)
        proxy = rotator.get_next_proxy()
    """

    def __init__(self, proxies: List[str], max_fails: int = 3):
        """
        Initialize proxy rotator.

        Args:
            proxies: List of proxy URLs
            max_fails: Max consecutive fails before marking proxy as dead
        """
        self.proxies = {url: ProxyInfo(url=url) for url in proxies}
        self.max_fails = max_fails
        self.current_index = 0
        self._lock = asyncio.Lock()

    def get_next_proxy(self) -> Optional[str]:
        """Get next working proxy in rotation."""
        working_proxies = [p for p in self.proxies.values() if p.is_working]

        if not working_proxies:
            logger.warning("No working proxies available!")
            return None

        # Round-robin selection
        proxy = working_proxies[self.current_index % len(working_proxies)]
        self.current_index = (self.current_index + 1) % len(working_proxies)

        proxy.last_used = datetime.utcnow()
        return proxy.url

    def get_random_proxy(self) -> Optional[str]:
        """Get random working proxy."""
        working_proxies = [p for p in self.proxies.values() if p.is_working]

        if not working_proxies:
            return None

        proxy = random.choice(working_proxies)
        proxy.last_used = datetime.utcnow()
        return proxy.url

    def get_best_proxy(self) -> Optional[str]:
        """Get proxy with best performance (highest success rate, lowest response time)."""
        working_proxies = [p for p in self.proxies.values() if p.is_working]

        if not working_proxies:
            return None

        # Score based on success rate and response time
        def score(proxy: ProxyInfo) -> float:
            total = proxy.success_count + proxy.fail_count
            if total == 0:
                return 0.5  # Neutral score for unused proxies

            success_rate = proxy.success_count / total
            # Lower response time is better, normalize to 0-1
            time_score = 1.0 / (1.0 + proxy.avg_response_time)

            return (success_rate * 0.7) + (time_score * 0.3)

        best_proxy = max(working_proxies, key=score)
        best_proxy.last_used = datetime.utcnow()
        return best_proxy.url

    async def mark_success(self, proxy_url: str, response_time: float):
        """Mark proxy request as successful."""
        async with self._lock:
            if proxy_url in self.proxies:
                proxy = self.proxies[proxy_url]
                proxy.success_count += 1

                # Update average response time
                total = proxy.success_count + proxy.fail_count
                proxy.avg_response_time = (
                    (proxy.avg_response_time * (total - 1) + response_time) / total
                )

                # Reset fail count on success
                proxy.fail_count = 0
                proxy.is_working = True

    async def mark_failure(self, proxy_url: str):
        """Mark proxy request as failed."""
        async with self._lock:
            if proxy_url in self.proxies:
                proxy = self.proxies[proxy_url]
                proxy.fail_count += 1

                # Mark as dead if too many failures
                if proxy.fail_count >= self.max_fails:
                    proxy.is_working = False
                    logger.warning(f"Proxy {proxy_url} marked as dead after {proxy.fail_count} failures")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about proxies."""
        working = sum(1 for p in self.proxies.values() if p.is_working)
        total = len(self.proxies)

        return {
            'total_proxies': total,
            'working_proxies': working,
            'dead_proxies': total - working,
            'proxies': [
                {
                    'url': p.url,
                    'is_working': p.is_working,
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                    'avg_response_time': p.avg_response_time,
                    'last_used': p.last_used.isoformat() if p.last_used else None,
                }
                for p in self.proxies.values()
            ]
        }


# ============================================================================
# STEALTH SCRAPER
# ============================================================================

class StealthScraper:
    """
    Universal stealth browser scraper with anti-detection features.

    Features:
    - User agent rotation
    - Proxy support with rotation
    - Browser fingerprinting evasion
    - Randomized behavior
    - Rate limiting
    - Session management

    Usage:
        scraper = StealthScraper()
        await scraper.start()
        page = await scraper.create_page()
        # Use page...
        await scraper.close()
    """

    def __init__(
        self,
        headless: bool = True,
        proxy_rotator: Optional[ProxyRotator] = None,
        rotate_user_agents: bool = True,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        enable_javascript: bool = True,
    ):
        """
        Initialize stealth scraper.

        Args:
            headless: Run browser in headless mode
            proxy_rotator: ProxyRotator instance for IP rotation
            rotate_user_agents: Whether to rotate user agents
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            enable_javascript: Enable JavaScript execution
        """
        self.headless = headless
        self.proxy_rotator = proxy_rotator
        self.rotate_user_agents = rotate_user_agents
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.enable_javascript = enable_javascript

        self.browser: Optional[Browser] = None
        self.playwright = None
        self.contexts: List[BrowserContext] = []

        # Rate limiting
        self.last_request_time = 0.0

        # Stats
        self.requests_count = 0
        self.success_count = 0
        self.fail_count = 0

    async def start(self):
        """Start the browser instance."""
        if self.browser:
            logger.warning("Browser already started")
            return

        logger.info("Starting Playwright browser for stealth scraping...")
        self.playwright = await async_playwright().start()

        # Browser launch arguments for maximum stealth
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--ignore-certificate-errors',
        ]

        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )

        logger.info("Stealth browser started successfully")

    async def close(self):
        """Close browser and cleanup."""
        # Close all contexts
        for context in self.contexts:
            await context.close()
        self.contexts.clear()

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("Stealth browser closed")

    async def create_page(self, custom_proxy: Optional[str] = None) -> Page:
        """
        Create a new page with full anti-detection setup.

        Args:
            custom_proxy: Optional custom proxy for this page

        Returns:
            Configured page with stealth features
        """
        if not self.browser:
            await self.start()

        # Select user agent
        user_agent = random.choice(USER_AGENTS) if self.rotate_user_agents else USER_AGENTS[0]

        # Select viewport
        viewport = random.choice(VIEWPORTS)

        # Select timezone and locale
        timezone = random.choice(TIMEZONES)
        locale = random.choice(LOCALES)

        # Determine proxy to use
        proxy = custom_proxy
        if not proxy and self.proxy_rotator:
            proxy = self.proxy_rotator.get_next_proxy()

        # Context options
        context_options = {
            'user_agent': user_agent,
            'viewport': viewport,
            'locale': locale,
            'timezone_id': timezone,
            'permissions': ['geolocation'],
            'geolocation': {
                'latitude': random.uniform(37.0, 41.0),  # US range
                'longitude': random.uniform(-125.0, -70.0)
            },
            'color_scheme': 'light',
            'device_scale_factor': random.choice([1, 1.5, 2]),
            'java_script_enabled': self.enable_javascript,
        }

        # Add proxy if available
        if proxy:
            context_options['proxy'] = {'server': proxy}
            logger.debug(f"Using proxy: {proxy}")

        # Create context
        context = await self.browser.new_context(**context_options)
        self.contexts.append(context)

        # Create page
        page = await context.new_page()

        # Inject anti-detection scripts
        await self._inject_stealth_scripts(page)

        logger.debug(f"Created stealth page - UA: {user_agent[:50]}..., Viewport: {viewport}")

        return page

    async def _inject_stealth_scripts(self, page: Page):
        """Inject comprehensive anti-detection JavaScript."""
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override the permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Chrome runtime
            window.chrome = {
                runtime: {}
            };

            // Override toString to hide modifications
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalToString.call(this);
            };

            // Mock battery API (common fingerprinting technique)
            Object.defineProperty(navigator, 'getBattery', {
                get: () => () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                })
            });

            // Mock connection API
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50,
                    saveData: false
                })
            });
        """)

    async def navigate_with_stealth(self, page: Page, url: str, wait_for: str = 'networkidle') -> bool:
        """
        Navigate to URL with rate limiting and randomization.

        Args:
            page: Page to navigate
            url: URL to navigate to
            wait_for: Wait condition ('load', 'domcontentloaded', 'networkidle')

        Returns:
            True if successful, False otherwise
        """
        # Rate limiting
        await self._apply_rate_limit()

        start_time = time.time()

        try:
            # Navigate
            await page.goto(url, wait_until=wait_for, timeout=30000)

            # Random delay after load (simulate reading)
            await asyncio.sleep(random.uniform(0.5, 2.0))

            # Track success
            response_time = time.time() - start_time
            self.requests_count += 1
            self.success_count += 1

            # Update proxy stats if using proxy
            if self.proxy_rotator and page.context.options.get('proxy'):
                proxy_url = page.context.options['proxy']['server']
                await self.proxy_rotator.mark_success(proxy_url, response_time)

            return True

        except Exception as e:
            logger.error(f"Navigation failed for {url}: {e}")
            self.requests_count += 1
            self.fail_count += 1

            # Update proxy stats if using proxy
            if self.proxy_rotator and page.context.options.get('proxy'):
                proxy_url = page.context.options['proxy']['server']
                await self.proxy_rotator.mark_failure(proxy_url)

            return False

    async def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        now = time.time()
        time_since_last = now - self.last_request_time

        delay_needed = random.uniform(self.min_delay, self.max_delay)

        if time_since_last < delay_needed:
            wait_time = delay_needed - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def scroll_page(self, page: Page, scrolls: int = 3):
        """Scroll page in human-like manner."""
        for i in range(scrolls):
            # Random scroll distance
            scroll_amount = random.randint(300, 800)
            await page.evaluate(f'window.scrollBy(0, {scroll_amount})')

            # Random delay
            await asyncio.sleep(random.uniform(0.5, 2.0))

    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        return {
            'requests_count': self.requests_count,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'success_rate': self.success_count / self.requests_count if self.requests_count > 0 else 0,
            'proxy_stats': self.proxy_rotator.get_stats() if self.proxy_rotator else None
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def create_stealth_scraper(proxies: Optional[List[str]] = None) -> StealthScraper:
    """
    Create and start a stealth scraper instance.

    Args:
        proxies: Optional list of proxy URLs

    Returns:
        Started StealthScraper instance
    """
    proxy_rotator = ProxyRotator(proxies) if proxies else None
    scraper = StealthScraper(proxy_rotator=proxy_rotator)
    await scraper.start()
    return scraper
