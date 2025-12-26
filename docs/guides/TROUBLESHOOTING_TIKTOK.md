# TikTok Auto-Ingestion Troubleshooting Guide

## 🚨 Common Issues & Solutions

Based on your logs, here are the issues and how to fix them:

---

## Issue 1: "Browser scraper returned no videos"

### Why This Happens:
- Playwright successfully launches browser
- But TikTok's anti-bot detection blocks the scraper
- Falls back to manual URL list

### Solutions:

#### Option A: Update TikTok Selectors (TikTok Changed DOM)

TikTok frequently changes their HTML structure. Update the selectors:

Edit `backend/app/tiktok_browser_scraper.py`:

```python
async def _extract_videos_from_page(self, page, feed_type, **metadata_overrides):
    """Extract video data from current page state."""
    videos = []

    try:
        # TikTok uses different selectors over time - try multiple strategies

        # Strategy 1: Modern TikTok (2024+)
        video_containers = await page.locator('[data-e2e="recommend-list-item-container"]').all()

        # Strategy 2: Alternative selector
        if not video_containers:
            video_containers = await page.locator('div[class*="DivItemContainer"]').all()

        # Strategy 3: Fallback to any video links
        if not video_containers:
            video_links = await page.locator('a[href*="/video/"]').all()

        for container in video_containers:
            try:
                # Extract video link
                link = await container.locator('a[href*="/video/"]').first
                href = await link.get_attribute('href')

                if not href or '/video/' not in href:
                    continue

                video_id = self._extract_video_id(href)
                if not video_id or video_id in self.seen_video_ids:
                    continue

                self.seen_video_ids.add(video_id)

                # Extract metadata
                metadata = await self._extract_video_metadata(page, link, container)

                video_data = {
                    'url': href if href.startswith('http') else f"https://www.tiktok.com{href}",
                    'video_id': video_id,
                    'feed_type': feed_type,
                    'scraped_at': datetime.utcnow().isoformat(),
                    **metadata,
                    **metadata_overrides
                }

                videos.append(video_data)

            except Exception as e:
                logger.debug(f"Error extracting video: {e}")
                continue

    except Exception as e:
        logger.error(f"Error extracting videos from page: {e}")

    return videos
```

#### Option B: Use Manual URL List (Temporary Workaround)

Create `backend/app/tiktok_urls.txt` with **real, working** TikTok URLs:

```bash
# Edit this file with actual TikTok video URLs
nano backend/app/tiktok_urls.txt
```

Add real URLs (one per line):
```
https://www.tiktok.com/@gordon_ramsay/video/7234567890123456789|cooking
https://www.tiktok.com/@nba/video/7234567890123456790|sports
https://www.tiktok.com/@jimmyfallon/video/7234567890123456791|comedy
```

**How to find URLs:**
1. Go to TikTok.com
2. Find a viral video
3. Copy the full URL
4. Paste in `tiktok_urls.txt` with category: `URL|category`

#### Option C: Disable Browser Scraping Temporarily

If scraping doesn't work, use manual mode:

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{"use_browser": false, "videos_per_fetch": 5}'
```

This will only use URLs from `tiktok_urls.txt`.

---

## Issue 2: "Your IP address is blocked"

### Why This Happens:
- TikTok detects automated access
- Your IP is temporarily blocked
- Too many requests in short time

### Solutions:

#### Solution 1: Use Proxies (Recommended for Production)

**Option A: Via API (Easiest)**

Use the proxy parameter when starting the ingestion service:

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "proxy": "http://your-proxy-server:port",
    "videos_per_fetch": 5
  }' | jq
```

**Option B: Via Environment Variable**

Add to your `.env` file:
```bash
TIKTOK_PROXY=http://your-proxy-server:port
```

Then modify `backend/app/tiktok_auto_ingestion.py` to read from env:
```python
import os

proxy = os.getenv("TIKTOK_PROXY")
service = TikTokAutoIngestion(
    use_browser=True,
    proxy=proxy
)
```

**Option C: Direct Code Modification**

Edit `backend/app/tiktok_browser_scraper.py`:

```python
class TikTokBrowserScraper:
    def __init__(
        self,
        headless: bool = True,
        max_videos: int = 50,
        scroll_delay: float = 2.0,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None  # NEW
    ):
        self.proxy = proxy
        # ...

    async def start(self):
        """Start the browser instance."""
        if self.browser:
            logger.warning("Browser already started")
            return

        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()

        # Launch browser with proxy
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ]

        # Add proxy if provided
        launch_options = {
            'headless': self.headless,
            'args': browser_args
        }

        if self.proxy:
            launch_options['proxy'] = {
                'server': self.proxy
            }
            logger.info(f"Using proxy: {self.proxy}")

        self.browser = await self.playwright.chromium.launch(**launch_options)
        logger.info("Browser started successfully")
```

Then use:
```python
# In tiktok_auto_ingestion.py
self.browser_scraper = TikTokBrowserScraper(
    max_videos=self.videos_per_fetch,
    proxy="http://proxy-server:port"  # Add your proxy
)
```

#### Solution 2: Increase Delays (Slower = Less Detection)

Edit `backend/app/tiktok_auto_ingestion.py`:

```python
# Increase fetch interval to avoid rate limiting
FETCH_INTERVAL = 600  # 10 minutes instead of 5
VIDEOS_PER_FETCH = 5   # Fewer videos per cycle
```

Edit `backend/app/tiktok_browser_scraper.py`:

```python
scraper = TikTokBrowserScraper(
    scroll_delay=5.0,  # Wait 5 seconds between scrolls (instead of 2)
)
```

#### Solution 3: Rotate User Agents

Edit `backend/app/tiktok_browser_scraper.py`:

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

class TikTokBrowserScraper:
    def __init__(self, ...):
        self.user_agent = random.choice(USER_AGENTS)
        # ...
```

#### Solution 4: Wait Before Retrying

TikTok blocks are usually temporary (15-60 minutes). Just wait and try again.

---

## Issue 3: "Unsupported URL" (Invalid URLs)

### Why This Happens:
Your `tiktok_urls.txt` has placeholder URLs like:
```
https://www.tiktok.com/@<realuser>/video/<realid>
```

These are templates, not real URLs!

### Solution:

Replace with **real TikTok URLs**:

```bash
# Remove placeholder URLs
rm backend/app/tiktok_urls.txt

# Create new file with real URLs
cat > backend/app/tiktok_urls.txt << 'EOF'
# Real TikTok video URLs - one per line
# Format: URL|category

# Example (replace with actual working URLs):
https://www.tiktok.com/@gordonramsayofficial/video/7123456789012345678|cooking
https://www.tiktok.com/@nba/video/7123456789012345679|sports
https://www.tiktok.com/@therock/video/7123456789012345680|fitness
EOF
```

**How to get real URLs:**
1. Open TikTok.com in your browser
2. Search for popular accounts (NBA, Gordon Ramsay, etc.)
3. Click on a video
4. Copy the full URL from browser
5. Paste in `tiktok_urls.txt`

---

## Quick Fix Summary

### Immediate Solution (Works Now):

1. **Create real URL list:**
```bash
cat > backend/app/tiktok_urls.txt << 'EOF'
https://www.tiktok.com/@gordonramsayofficial/video/7330819518867598634|cooking
https://www.tiktok.com/@nba/video/7330567890123456789|sports
https://www.tiktok.com/@therock/video/7330987654321098765|fitness
EOF
```

2. **Disable browser scraping temporarily:**
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{"use_browser": false, "videos_per_fetch": 3}'
```

3. **Verify it works:**
```bash
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq
```

### Long-term Solution:

1. **Use residential proxies** (services like Bright Data, SmartProxy)
2. **Rotate user agents and IPs**
3. **Increase delays** between requests
4. **Use VPN** when developing

---

## Alternative: Use TikTok API (Best Solution)

### TikTok Official API

Instead of scraping, use TikTok's official API:

1. Apply for TikTok Developer Account: https://developers.tiktok.com/
2. Get API credentials
3. Use official endpoints

**Pros:**
- No IP blocking
- No DOM changes
- Faster and more reliable
- Legal and compliant

**Cons:**
- Requires approval
- Limited access
- May have rate limits

---

## Testing Without TikTok

### Use Demo Videos Instead

Disable TikTok ingestion and use demo videos:

Edit `.env`:
```bash
ENABLE_TIKTOK_AUTO_INGEST=false
INGEST_DEMO_VIDEOS=true
DEMO_VIDEO_COUNT=20
```

Restart backend:
```bash
bash START_TIKTOK_PLATFORM.sh
```

You'll get 20 demo videos to test your feed without TikTok scraping.

---

## Monitoring & Debugging

### Check What's Actually Happening

```bash
# Watch logs in real-time
tail -f backend/logs/app.log | grep -i tiktok

# Check ingestion status
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq

# See what videos are in database
curl 'http://localhost:8080/api/v1/feed/for-you?user_id=user:test&limit=10' | jq '.videos | length'
```

### Run Scraper Manually (See What Happens)

```bash
cd backend
python -m app.tiktok_browser_scraper
```

This will show you exactly where it fails.

---

## Summary: What to Do Now

### Option 1: Quick Fix (Manual URLs)
1. Create `tiktok_urls.txt` with real URLs
2. Disable browser scraping
3. Videos will download from manual list

### Option 2: Fix Browser Scraping
1. Wait 30-60 minutes (IP block expires)
2. Increase delays (slower scraping)
3. Try again

### Option 3: Use Demo Videos
1. Disable TikTok ingestion
2. Enable demo videos
3. Test your platform

**Choose based on your needs!** For immediate testing, use demo videos. For production, fix browser scraping or use TikTok API.

---

## Still Not Working?

Check these:
1. ✅ Playwright installed? `playwright --version`
2. ✅ yt-dlp installed? `yt-dlp --version`
3. ✅ Internet connection working?
4. ✅ No VPN interfering?
5. ✅ Logs show any other errors?

Run this diagnostic:
```bash
# Test all components
playwright --version
yt-dlp --version
curl -I https://www.tiktok.com
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

If all pass, the issue is TikTok's anti-bot detection. Use solutions above!
