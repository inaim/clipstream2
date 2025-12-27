# Stealth Scraper Library

A universal, reusable anti-detection library for web scraping that can be used across multiple projects.

## 🎯 Features

### Core Features
- ✅ **User Agent Rotation** - 20+ realistic browser fingerprints
- ✅ **Proxy Rotation** - Automatic proxy switching with health monitoring
- ✅ **Browser Fingerprinting Evasion** - Advanced JavaScript injection
- ✅ **Randomized Behavior** - Human-like scrolling, delays, and navigation
- ✅ **Rate Limiting** - Prevent triggering anti-bot systems
- ✅ **Session Management** - Multiple browser contexts
- ✅ **Performance Tracking** - Monitor success rates and proxy health

### Anti-Detection Techniques
- Removes `navigator.webdriver` property
- Mocks browser plugins and permissions
- Randomizes viewports, timezones, and locales
- Implements human-like delays and behavior
- Battery API mocking
- Connection API mocking
- toString overrides to hide modifications

---

## 📦 Installation

Already included in the `backend/lib/` directory. No additional installation needed.

**Dependencies:**
```bash
pip install playwright
playwright install chromium
```

---

## 🚀 Quick Start

### Basic Usage

```python
from lib.stealth_scraper import StealthScraper

# Create scraper
scraper = StealthScraper()
await scraper.start()

# Create a stealth page
page = await scraper.create_page()

# Navigate to target site
await scraper.navigate_with_stealth(page, "https://example.com")

# Extract data
data = await page.content()

# Cleanup
await scraper.close()
```

### With Proxy Rotation

```python
from lib.stealth_scraper import StealthScraper, ProxyRotator

# Define your proxies
proxies = [
    "http://proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:3128",
    "http://proxy3.example.com:8888",
]

# Create proxy rotator
proxy_rotator = ProxyRotator(proxies)

# Create scraper with proxy rotation
scraper = StealthScraper(proxy_rotator=proxy_rotator)
await scraper.start()

# Pages will automatically use rotating proxies
page = await scraper.create_page()
await scraper.navigate_with_stealth(page, "https://example.com")

# Check proxy stats
stats = proxy_rotator.get_stats()
print(f"Working proxies: {stats['working_proxies']}/{stats['total_proxies']}")
```

### Context Manager (Recommended)

```python
from lib.stealth_scraper import create_stealth_scraper

async def scrape_website():
    proxies = ["http://proxy1:8080", "http://proxy2:8080"]

    async with await create_stealth_scraper(proxies) as scraper:
        page = await scraper.create_page()
        await scraper.navigate_with_stealth(page, "https://example.com")

        # Scroll like a human
        await scraper.scroll_page(page, scrolls=5)

        # Extract data
        content = await page.content()
        return content
```

---

## 📚 Detailed Usage

### ProxyRotator

Manages a pool of proxies with automatic rotation and health tracking.

```python
from lib.stealth_scraper import ProxyRotator

# Initialize with proxy list
proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
rotator = ProxyRotator(proxies, max_fails=3)

# Get next proxy (round-robin)
proxy = rotator.get_next_proxy()

# Get random proxy
proxy = rotator.get_random_proxy()

# Get best performing proxy
proxy = rotator.get_best_proxy()

# Mark proxy results
await rotator.mark_success(proxy_url, response_time=1.5)
await rotator.mark_failure(proxy_url)

# Get statistics
stats = rotator.get_stats()
# {
#   'total_proxies': 3,
#   'working_proxies': 2,
#   'dead_proxies': 1,
#   'proxies': [...]
# }
```

### StealthScraper

Main scraper class with full anti-detection features.

#### Configuration Options

```python
scraper = StealthScraper(
    headless=True,                  # Run browser in headless mode
    proxy_rotator=proxy_rotator,    # ProxyRotator instance (optional)
    rotate_user_agents=True,        # Rotate user agents on each page
    min_delay=1.0,                  # Min delay between requests (seconds)
    max_delay=3.0,                  # Max delay between requests (seconds)
    enable_javascript=True,         # Enable JavaScript execution
)
```

#### Navigation

```python
# Navigate with automatic rate limiting and stealth
success = await scraper.navigate_with_stealth(
    page,
    "https://example.com",
    wait_for='networkidle'  # 'load', 'domcontentloaded', 'networkidle'
)

if success:
    print("Navigation successful")
else:
    print("Navigation failed")
```

#### Human-Like Scrolling

```python
# Scroll page like a human (random delays and scroll amounts)
await scraper.scroll_page(page, scrolls=5)
```

#### Statistics

```python
# Get scraper statistics
stats = scraper.get_stats()
# {
#   'requests_count': 100,
#   'success_count': 95,
#   'fail_count': 5,
#   'success_rate': 0.95,
#   'proxy_stats': {...}
# }
```

---

## 🎮 Integration with TikTok Scraper

The stealth scraper is already integrated into the TikTok browser scraper:

### Enable Stealth Mode

```python
from app.tiktok_browser_scraper import TikTokBrowserScraper

# Create scraper
scraper = TikTokBrowserScraper()
await scraper.start()

# Enable advanced stealth mode with proxy rotation
proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080"
]
await scraper.enable_stealth_mode(proxies=proxies)

# Now all pages will use advanced anti-detection
videos = await scraper.scrape_trending_feed(limit=20)
```

### API Integration

You can also enable it via the API:

```bash
# Start ingestion with stealth mode
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "use_stealth_mode": true,
    "proxies": ["http://proxy1:8080", "http://proxy2:8080"],
    "videos_per_fetch": 10
  }'
```

---

## 🔧 Advanced Usage

### Custom Proxy Selection Strategies

```python
# Get specific proxy for a page
proxy = rotator.get_best_proxy()  # Get proxy with best success rate
page = await scraper.create_page(custom_proxy=proxy)
```

### Multiple Concurrent Sessions

```python
# Create multiple pages with different proxies
pages = []
for i in range(5):
    page = await scraper.create_page()
    pages.append(page)

# Each page uses different proxy and fingerprint
await asyncio.gather(*[
    scraper.navigate_with_stealth(page, url)
    for page, url in zip(pages, urls)
])
```

### Monitoring Proxy Health

```python
# Continuously monitor proxy health
while True:
    stats = rotator.get_stats()

    for proxy in stats['proxies']:
        if proxy['is_working']:
            success_rate = proxy['success_count'] / (proxy['success_count'] + proxy['fail_count'])
            print(f"{proxy['url']}: {success_rate:.2%} success, {proxy['avg_response_time']:.2f}s avg")

    await asyncio.sleep(60)  # Check every minute
```

---

## 📊 Use Cases

### 1. E-commerce Price Monitoring

```python
async def monitor_prices():
    proxies = ["http://proxy1:8080", "http://proxy2:8080"]
    scraper = await create_stealth_scraper(proxies)

    urls = [
        "https://amazon.com/product1",
        "https://ebay.com/product2",
        "https://walmart.com/product3"
    ]

    for url in urls:
        page = await scraper.create_page()
        await scraper.navigate_with_stealth(page, url)

        # Extract price
        price = await page.locator('.price').text_content()
        print(f"{url}: ${price}")

    await scraper.close()
```

### 2. Social Media Scraping

```python
async def scrape_social_media():
    proxies = get_proxies_from_file()  # Load from config
    scraper = await create_stealth_scraper(proxies)

    page = await scraper.create_page()
    await scraper.navigate_with_stealth(page, "https://twitter.com/trending")

    # Scroll to load more content
    await scraper.scroll_page(page, scrolls=10)

    # Extract trending topics
    topics = await page.locator('.trending-item').all_text_contents()

    await scraper.close()
    return topics
```

### 3. News Aggregation

```python
async def aggregate_news():
    scraper = await create_stealth_scraper()

    news_sites = [
        "https://news.ycombinator.com",
        "https://techcrunch.com",
        "https://reddit.com/r/programming"
    ]

    articles = []
    for site in news_sites:
        page = await scraper.create_page()
        if await scraper.navigate_with_stealth(page, site):
            # Extract articles
            titles = await page.locator('h2').all_text_contents()
            articles.extend(titles)

    await scraper.close()
    return articles
```

---

## 🛡️ Free Proxy Sources

### Where to Find Free Proxies

1. **Proxy List Download** - https://www.proxy-list.download/
2. **Free Proxy List** - https://free-proxy-list.net/
3. **ProxyScrape** - https://proxyscrape.com/free-proxy-list
4. **GeoNode** - https://geonode.com/free-proxy-list

### Loading Proxies from File

```python
def load_proxies(filename: str) -> List[str]:
    """Load proxies from a text file."""
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies

# Usage
proxies = load_proxies('proxies.txt')
scraper = await create_stealth_scraper(proxies)
```

### Validating Proxies

```python
async def validate_proxy(proxy_url: str) -> bool:
    """Test if a proxy is working."""
    scraper = StealthScraper()
    await scraper.start()

    try:
        page = await scraper.create_page(custom_proxy=proxy_url)
        success = await scraper.navigate_with_stealth(page, "https://httpbin.org/ip")
        await scraper.close()
        return success
    except:
        await scraper.close()
        return False

# Filter working proxies
proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
working_proxies = [p for p in proxies if await validate_proxy(p)]
```

---

## 📈 Performance Tips

1. **Use Proxy Rotation** - Prevents IP bans and rate limiting
2. **Adjust Delays** - Balance speed vs detection risk
3. **Monitor Success Rates** - Watch for patterns in failures
4. **Rotate User Agents** - Makes each request look different
5. **Use Headless Mode** - Faster and uses less resources
6. **Limit Concurrent Requests** - Don't overwhelm target or proxies
7. **Cache Proxy Performance** - Use best-performing proxies more often

---

## 🔒 Best Practices

### 1. Respect Robots.txt
```python
# Check robots.txt before scraping
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()

if rp.can_fetch("*", "https://example.com/products"):
    # Scrape
    pass
```

### 2. Implement Rate Limiting
```python
# Built-in rate limiting
scraper = StealthScraper(
    min_delay=2.0,  # At least 2 seconds between requests
    max_delay=5.0   # Up to 5 seconds
)
```

### 3. Handle Errors Gracefully
```python
try:
    success = await scraper.navigate_with_stealth(page, url)
    if not success:
        logger.warning(f"Failed to navigate to {url}")
        # Try with different proxy
        proxy = rotator.get_next_proxy()
        page = await scraper.create_page(custom_proxy=proxy)
        await scraper.navigate_with_stealth(page, url)
except Exception as e:
    logger.error(f"Scraping error: {e}")
    # Implement backoff strategy
```

### 4. Monitor and Alert
```python
# Send alerts when success rate drops
stats = scraper.get_stats()
if stats['success_rate'] < 0.5:
    send_alert("Scraper success rate below 50%!")
```

---

## 🆘 Troubleshooting

### Issue: All Proxies Marked as Dead

**Cause:** Proxies are failing health checks

**Solutions:**
- Use premium proxies instead of free ones
- Increase `max_fails` threshold
- Validate proxies before adding to rotator

### Issue: Still Getting Blocked

**Causes:**
- Website has advanced bot detection
- Proxies are datacenter IPs (easily detected)

**Solutions:**
- Use residential proxies
- Increase delays between requests
- Reduce concurrent requests
- Check if site requires login/cookies

### Issue: Slow Performance

**Solutions:**
- Use headless mode: `StealthScraper(headless=True)`
- Reduce delays: `min_delay=0.5, max_delay=1.0`
- Limit concurrent pages
- Use faster proxies

---

## 📝 Example: Complete Scraping Project

```python
import asyncio
from lib.stealth_scraper import StealthScraper, ProxyRotator
from typing import List, Dict

class UniversalScraper:
    """Universal web scraper using stealth library."""

    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies
        self.scraper = None

    async def start(self):
        """Initialize scraper."""
        proxy_rotator = ProxyRotator(self.proxies) if self.proxies else None
        self.scraper = StealthScraper(
            proxy_rotator=proxy_rotator,
            min_delay=1.0,
            max_delay=2.0
        )
        await self.scraper.start()

    async def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple URLs concurrently."""
        results = []

        for url in urls:
            page = await self.scraper.create_page()
            success = await self.scraper.navigate_with_stealth(page, url)

            if success:
                content = await page.content()
                results.append({'url': url, 'content': content})
            else:
                results.append({'url': url, 'error': 'Failed to load'})

        return results

    async def close(self):
        """Cleanup."""
        if self.scraper:
            await self.scraper.close()

    def get_stats(self):
        """Get scraping statistics."""
        return self.scraper.get_stats()

# Usage
async def main():
    proxies = load_proxies('proxies.txt')
    scraper = UniversalScraper(proxies)

    await scraper.start()

    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]

    results = await scraper.scrape_multiple_urls(urls)

    for result in results:
        print(f"URL: {result['url']}")
        print(f"Success: {'error' not in result}")

    # Show stats
    stats = scraper.get_stats()
    print(f"Success Rate: {stats['success_rate']:.2%}")

    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎓 Summary

The Stealth Scraper library provides:

✅ **Reusable** - Use across any Python project
✅ **Powerful** - Advanced anti-detection techniques
✅ **Flexible** - Configurable for different use cases
✅ **Reliable** - Automatic proxy rotation and health monitoring
✅ **Production-Ready** - Error handling, rate limiting, statistics

Perfect for:
- Web scraping projects
- Price monitoring
- Social media data collection
- News aggregation
- Market research
- SEO monitoring
- Any automated browser tasks

---

## 📄 License

Part of the Clipstream platform. Free to use in any project.
