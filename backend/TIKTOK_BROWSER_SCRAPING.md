# TikTok Browser Scraping Guide

Real-time TikTok video feed scraping using headless browser automation with Playwright.

## Overview

The TikTok browser scraper uses Playwright to automate a headless browser that navigates TikTok feeds and extracts video URLs and metadata through infinite scrolling. This enables real-time ingestion of trending videos without relying on TikTok's official API.

## Features

- **Headless Browser Automation**: Uses Playwright/Chromium for JavaScript-rendered content
- **Infinite Scroll Support**: Continuously scrolls to load more videos
- **Multi-Source Scraping**:
  - Trending feed (`/foryou`)
  - Hashtag feeds (`/tag/{hashtag}`)
  - User profiles (`/@{username}`)
- **Metadata Extraction**: Extracts titles, descriptions, creators, hashtags, view counts, likes
- **Anti-Detection Measures**: User agent spoofing, viewport settings, automation flags disabled
- **Concurrent Scraping**: Scrape multiple hashtags in parallel
- **Automatic Integration**: Works with existing auto-ingestion pipeline

## Installation

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This includes:
- `playwright` - Browser automation framework
- `yt-dlp` - Video download tool (existing)

### 2. Install Playwright Browsers

After installing the Python package, install the Chromium browser:

```bash
playwright install chromium
```

Or install all browsers:

```bash
playwright install
```

## Usage

### Option 1: Auto-Ingestion Service (Recommended)

The auto-ingestion service now supports browser scraping by default.

#### Start with Browser Scraping (Default)

```bash
# Via API
curl -X POST http://localhost:8000/api/tiktok_ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "fetch_interval": 300,
    "videos_per_fetch": 20,
    "use_browser": true
  }'
```

#### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fetch_interval` | int | 300 | Seconds between fetch cycles (60-3600) |
| `videos_per_fetch` | int | 10 | Videos to fetch per cycle (1-50) |
| `use_browser` | bool | true | Enable browser scraping for feed discovery |

#### Check Status

```bash
curl http://localhost:8000/api/tiktok_ingestion/status
```

Response:
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "fetch_interval": 300,
    "videos_per_fetch": 20,
    "use_browser": true,
    "total_fetched": 45,
    "total_ingested": 42,
    "total_failed": 3,
    "success_rate": 0.933,
    "last_fetch_time": 1703012345.67
  }
}
```

#### Stop Service

```bash
curl -X POST http://localhost:8000/api/tiktok_ingestion/stop
```

### Option 2: Direct Scraper Usage (Python)

Use the scraper directly in your Python code:

```python
from app.tiktok_browser_scraper import TikTokBrowserScraper

# Example 1: Scrape trending feed
async with TikTokBrowserScraper(max_videos=50) as scraper:
    videos = await scraper.scrape_trending_feed(limit=20)

    for video in videos:
        print(f"Video: {video['url']}")
        print(f"  Description: {video['description']}")
        print(f"  Creator: @{video['creator']}")
        print(f"  Hashtags: {video['hashtags']}")
        print(f"  Views: {video['view_count']}")
        print()

# Example 2: Scrape specific hashtag
async with TikTokBrowserScraper() as scraper:
    videos = await scraper.scrape_hashtag_feed('viral', limit=30)

# Example 3: Scrape user profile
async with TikTokBrowserScraper() as scraper:
    videos = await scraper.scrape_user_videos('username', limit=15)

# Example 4: Scrape multiple hashtags concurrently
async with TikTokBrowserScraper() as scraper:
    hashtags = ['fyp', 'viral', 'funny', 'cooking']
    videos = await scraper.scrape_multiple_hashtags(
        hashtags=hashtags,
        videos_per_hashtag=10
    )
```

### Option 3: Standalone Script

Run the example script:

```bash
cd backend
python -m app.tiktok_browser_scraper
```

## How It Works

### 1. Feed Discovery (Browser Scraping)

```
Browser Launch → Navigate to TikTok → Infinite Scroll → Extract Video URLs
```

The scraper:
1. Launches headless Chromium browser
2. Navigates to TikTok feed (trending, hashtag, or user)
3. Waits for content to load
4. Scrolls down repeatedly to trigger infinite scroll
5. Extracts video URLs and metadata from DOM
6. Continues until reaching limit or no new videos

### 2. Video Download (yt-dlp)

```
Video URLs → yt-dlp Download → Extract Metadata → Store Locally
```

Once video URLs are discovered:
1. Downloads video using yt-dlp (without watermark)
2. Extracts detailed metadata from yt-dlp info.json
3. Merges browser-scraped metadata with download metadata
4. Computes content hash

### 3. Database Ingestion

```
Video Files → Upload to Storage → Create DB Record → Publish Events
```

Final step:
1. Stores video file in uploads directory (or CDN)
2. Creates video record in SurrealDB
3. Publishes real-time events to Redis
4. Makes video available in feeds

## Configuration

### Trending Hashtags

Edit the hashtags used for scraping in `backend/app/tiktok_auto_ingestion.py`:

```python
TRENDING_HASHTAGS = [
    "fyp", "foryou", "viral", "trending",
    "funny", "comedy", "sports", "music",
    "gaming", "dance", "cooking", "travel"
]
```

### Browser Settings

Customize browser behavior in `TikTokBrowserScraper.__init__()`:

```python
scraper = TikTokBrowserScraper(
    headless=True,           # Run in headless mode
    max_videos=50,           # Max videos per session
    scroll_delay=2.0,        # Seconds between scrolls
    user_agent="..."         # Custom user agent
)
```

### Scraping Strategy

The scraper uses multiple strategies to find video elements:

1. **Link Selectors**: Finds `<a>` tags with `/video/` in href
2. **Container Detection**: Looks for TikTok's data-e2e attributes
3. **Metadata Extraction**: Parses descriptions, usernames, stats from DOM
4. **Duplicate Prevention**: Tracks seen video IDs to avoid re-processing

## Fallback Mechanism

If browser scraping fails or is disabled, the system falls back to manual URL lists:

Create `backend/app/tiktok_urls.txt`:

```
https://www.tiktok.com/@user/video/123456789|funny
https://www.tiktok.com/@user/video/987654321|cooking
https://www.tiktok.com/@user/video/555555555|trending
```

Format: `URL|category` (one per line, # for comments)

## Monitoring & Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Run in Non-Headless Mode

See the browser in action:

```python
scraper = TikTokBrowserScraper(headless=False)
```

### Check Scraper Output

```bash
# Trigger manual ingestion
curl -X POST http://localhost:8000/api/tiktok_ingestion/trigger-now

# Check logs
tail -f backend/logs/app.log
```

## Rate Limiting & Best Practices

### Recommended Settings

- **Fetch Interval**: 300-600 seconds (5-10 minutes)
- **Videos Per Fetch**: 10-20 videos
- **Scroll Delay**: 2-3 seconds

### Avoiding Rate Limits

1. **Use reasonable delays**: Don't scrape too aggressively
2. **Rotate user agents**: Randomize browser fingerprints
3. **Use proxies**: Consider rotating proxies for production
4. **Monitor failures**: Watch `total_failed` in status API
5. **Respect TOS**: Ensure compliance with TikTok's terms of service

## Troubleshooting

### Issue: Playwright not found

**Solution**: Install Playwright browsers
```bash
playwright install chromium
```

### Issue: Browser crashes or timeouts

**Solution**: Increase timeout or reduce concurrent requests
```python
await page.goto(url, timeout=60000)  # 60 second timeout
```

### Issue: No videos extracted

**Solution**:
1. Check if TikTok changed their DOM structure
2. Run in non-headless mode to inspect page
3. Update selectors in `_extract_videos_from_page()`

### Issue: Videos fail to download

**Solution**:
1. Verify yt-dlp is installed: `yt-dlp --version`
2. Update yt-dlp: `pip install -U yt-dlp`
3. Check video URL format is correct

## API Integration

### Start Auto-Ingestion with Browser Scraping

```javascript
// JavaScript/TypeScript
const response = await fetch('http://localhost:8000/api/tiktok_ingestion/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    fetch_interval: 300,
    videos_per_fetch: 20,
    use_browser: true
  })
});

const result = await response.json();
console.log('Ingestion started:', result.status);
```

### Monitor Real-Time Events

```javascript
// Listen to real-time video creation events
const eventSource = new EventSource('http://localhost:8000/api/videos/events/global');

eventSource.addEventListener('video_created', (event) => {
  const video = JSON.parse(event.data);
  console.log('New TikTok video ingested:', video);
});
```

## Performance

### Typical Performance Metrics

- **Browser startup**: ~2-3 seconds
- **Page load**: ~3-5 seconds
- **Scraping 20 videos**: ~15-30 seconds (with scrolling)
- **Video download**: ~5-10 seconds per video (depends on size)
- **Total cycle time**: ~3-5 minutes for 20 videos

### Optimization Tips

1. **Parallel downloads**: Enabled by default in `TikTokScraper.download_multiple()`
2. **Concurrent hashtag scraping**: Use `scrape_multiple_hashtags()`
3. **Reuse browser instance**: Keep browser alive between fetches
4. **Cache sessions**: Store cookies to reduce login/verification prompts

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│  TikTok Auto-Ingestion Service              │
│  (Runs every N minutes)                     │
└──────────────┬──────────────────────────────┘
               │
               ├─> Browser Scraper (Playwright)
               │   └─> Scrapes trending hashtags
               │       └─> Returns video URLs + metadata
               │
               ├─> Video Downloader (yt-dlp)
               │   └─> Downloads videos from URLs
               │       └─> Extracts metadata
               │
               ├─> Database Ingestion
               │   └─> Creates video records
               │       └─> Stores in SurrealDB
               │
               └─> Event Publishing
                   └─> Publishes to Redis
                       └─> Updates real-time feeds
```

## Security Considerations

1. **TOS Compliance**: Ensure scraping complies with TikTok's Terms of Service
2. **Rate Limiting**: Implement proper delays to avoid IP bans
3. **User Agents**: Rotate user agents to appear as regular browsers
4. **Proxies**: Use residential proxies for production deployments
5. **Content Rights**: Respect copyright and creator rights
6. **Data Privacy**: Handle user data according to privacy regulations

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt && playwright install`
2. **Start the service**: POST to `/api/tiktok_ingestion/start`
3. **Monitor status**: GET `/api/tiktok_ingestion/status`
4. **View ingested videos**: Check your video feeds at `/api/feed/for-you`

## Support

For issues or questions:
1. Check the logs: `backend/logs/app.log`
2. Review this documentation
3. Inspect the code: `backend/app/tiktok_browser_scraper.py`
