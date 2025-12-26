# 🎬 TikTok Auto-Ingestion Guide - Complete Documentation

## What is This?

**Automatic TikTok video ingestion with browser scraping** - A background service that continuously:
- Scrapes trending TikTok videos using headless browser (Playwright)
- Uses infinite scroll to discover new content
- Downloads videos with yt-dlp (no watermark)
- Extracts metadata (views, likes, hashtags, creator)
- Ingests into your database automatically
- Makes videos available in your real-time ML feed

---

## 🚀 Quick Start - One Command!

```bash
bash START_TIKTOK_PLATFORM.sh
```

That's it! This will:
1. ✅ Start SurrealDB and Redis
2. ✅ Install dependencies (yt-dlp, Playwright)
3. ✅ Enable TikTok auto-ingestion automatically
4. ✅ Start browser scraping every 5 minutes
5. ✅ Videos appear in your feed automatically!

---

## 📋 Prerequisites

### Required:
- Docker (for SurrealDB and Redis)
- Python 3.8+
- pip

### Auto-Installed by START_TIKTOK_PLATFORM.sh:
- yt-dlp (video downloader)
- Playwright (browser automation)
- Chromium browser

Or install manually:
```bash
pip install yt-dlp playwright
playwright install chromium
```

---

## 🎯 How It Works

### Architecture Flow:

```
START_TIKTOK_PLATFORM.sh
         ↓
Backend starts (ENABLE_TIKTOK_AUTO_INGEST=true)
         ↓
Auto-ingestion service starts
         ↓
Every 5 minutes:
    ↓
    Browser Launch (Headless Chromium)
    ↓
    Navigate to TikTok hashtags (#fyp, #viral, etc.)
    ↓
    Infinite Scroll (load more videos)
    ↓
    Extract Video URLs + Metadata
    ↓
    Download Videos (yt-dlp)
    ↓
    Ingest to Database (SurrealDB)
    ↓
    Publish Events (Redis)
    ↓
Videos Available in Feeds!
```

### What Gets Scraped:

**Default Trending Hashtags:**
- #fyp (For You Page)
- #foryou
- #viral
- #trending
- #funny
- #comedy
- #sports
- #music
- #gaming
- #dance
- #cooking
- #travel

**Metadata Extracted:**
- Video URL and ID
- Title and description
- Creator username
- View count
- Like count
- Comment count
- Share count
- Hashtags
- Upload date

---

## ⚙️ Configuration

### Auto-Start Configuration (Default: Enabled)

Auto-ingestion starts automatically when you run `START_TIKTOK_PLATFORM.sh`.

To **disable** auto-start, add to your `.env`:
```bash
ENABLE_TIKTOK_AUTO_INGEST=false
```

### Scraping Parameters

Edit `backend/app/tiktok_auto_ingestion.py`:

```python
# Fetch interval (seconds)
FETCH_INTERVAL = 300  # 5 minutes (default)

# Videos per fetch cycle
VIDEOS_PER_FETCH = 10  # default

# Trending hashtags to scrape
TRENDING_HASHTAGS = [
    "fyp", "foryou", "viral", "trending",
    "funny", "comedy", "sports", "music",
    "gaming", "dance", "cooking", "travel"
]
```

### Browser Settings

Edit `backend/app/tiktok_browser_scraper.py`:

```python
scraper = TikTokBrowserScraper(
    headless=True,           # Run in headless mode
    max_videos=50,           # Max videos per session
    scroll_delay=2.0,        # Seconds between scrolls
    user_agent="..."         # Custom user agent
)
```

---

## 🎛️ API Control

### Check Status

```bash
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq
```

Response:
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "use_browser": true,
    "fetch_interval": 300,
    "videos_per_fetch": 10,
    "total_fetched": 45,
    "total_ingested": 42,
    "total_failed": 3,
    "success_rate": 0.933,
    "last_fetch_time": 1703012345.67
  }
}
```

### Start Service (with custom config)

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "fetch_interval": 180,
    "videos_per_fetch": 20
  }' | jq
```

### Stop Service

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq
```

### Trigger Manual Fetch

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/trigger-now | jq
```

---

## 📺 Accessing Videos in Frontend

### Option 1: For You Feed (ML-Ranked)

```javascript
const response = await fetch('http://localhost:8080/api/v1/feed/for-you?user_id=user:123&limit=20');
const data = await response.json();
const videos = data.videos;
```

### Option 2: Infinite Scroll Feed

```javascript
// Initial load
const response = await fetch('http://localhost:8080/api/v1/infinite/feed?limit=10');
const { videos, next_cursor } = await response.json();

// Load more
const loadMore = await fetch(`http://localhost:8080/api/v1/infinite/feed?cursor=${next_cursor}`);
```

### Option 3: Real-time Updates (SSE)

```javascript
const eventSource = new EventSource('http://localhost:8080/api/videos/events/global');

eventSource.addEventListener('video_created', (event) => {
  const newVideo = JSON.parse(event.data);
  console.log('New TikTok video:', newVideo);
});
```

### Complete React Example

```tsx
import { useEffect, useState } from 'react';

interface Video {
  id: string;
  title: string;
  cdn_url: string;
  creator_name: string;
  view_count: number;
  like_count: number;
  hashtags: string[];
}

export default function TikTokFeed({ userId }: { userId: string }) {
  const [videos, setVideos] = useState<Video[]>([]);

  useEffect(() => {
    fetchVideos();
    const interval = setInterval(fetchVideos, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [userId]);

  const fetchVideos = async () => {
    const res = await fetch(`http://localhost:8080/api/v1/feed/for-you?user_id=${userId}&limit=20`);
    const data = await res.json();
    setVideos(data.videos || []);
  };

  return (
    <div className="video-feed">
      {videos.map(video => (
        <div key={video.id} className="video-card">
          <video src={video.cdn_url} controls />
          <h3>{video.title}</h3>
          <p>@{video.creator_name}</p>
          <span>👁️ {video.view_count} ❤️ {video.like_count}</span>
        </div>
      ))}
    </div>
  );
}
```

---

## 🔍 Monitoring & Debugging

### View Backend Logs

```bash
# Logs show auto-ingestion activity
tail -f backend/logs/app.log
```

Look for:
```
[STEP 3.5] Starting TikTok auto-ingestion with browser scraping...
✅ TikTok auto-ingestion service started (browser scraping enabled)
   - Scraping trending hashtags every 5 minutes
   - Browser: Headless Chromium with infinite scroll

Using browser scraper to fetch trending videos
Browser scraper found 10 videos
Ingested: TikTok Video Title
Batch complete: 8 ingested, 2 failed
```

### Run in Non-Headless Mode (See Browser)

Edit `backend/app/tiktok_browser_scraper.py`:
```python
scraper = TikTokBrowserScraper(headless=False)  # Show browser window
```

### Test Scraper Directly

```bash
cd backend
python -m app.tiktok_browser_scraper
```

---

## 🛠️ Troubleshooting

### Issue: Playwright not found

**Error:**
```
BrowserType.launch: Executable doesn't exist
```

**Solution:**
```bash
pip install playwright
playwright install chromium
```

### Issue: No videos being scraped

**Check:**
1. Browser scraping enabled? Check status API
2. Playwright installed? Run `playwright --version`
3. Internet connection working?
4. Check logs for errors

**Debug:**
```bash
# Run scraper manually
cd backend
python -m app.tiktok_browser_scraper

# Check API status
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq
```

### Issue: Videos fail to download

**Error:** `yt-dlp failed`

**Solution:**
```bash
# Update yt-dlp
pip install -U yt-dlp

# Test manually
yt-dlp "https://www.tiktok.com/@user/video/123"
```

### Issue: Auto-ingestion not starting

**Check:**
1. Environment variable set?
   ```bash
   echo $ENABLE_TIKTOK_AUTO_INGEST
   ```
2. Backend logs show Step 3.5?
3. Using latest `main.py`?

---

## 📊 Performance & Best Practices

### Recommended Settings

```python
# Good for development
FETCH_INTERVAL = 300  # 5 minutes
VIDEOS_PER_FETCH = 10

# Good for production
FETCH_INTERVAL = 600  # 10 minutes
VIDEOS_PER_FETCH = 20
```

### Rate Limiting Tips

1. **Don't scrape too frequently** - TikTok may rate limit
2. **Use reasonable delays** - 2-3 seconds between scrolls
3. **Rotate user agents** - Randomize browser fingerprints
4. **Monitor success rate** - Should be >80%

### Storage Considerations

```bash
# Each video ~5-20MB
# 10 videos/5min = 120 videos/hour = ~1-2GB/hour
# Plan storage accordingly
```

---

## 🔐 Security & Compliance

### Important Notes:

1. **TikTok ToS** - Ensure compliance with TikTok's terms of service
2. **Copyright** - Respect creator rights and copyright
3. **Rate Limits** - Don't abuse TikTok's servers
4. **Content Moderation** - Filter inappropriate content
5. **User Data** - Handle metadata according to privacy laws

### Content Filtering

Add to `backend/app/tiktok_auto_ingestion.py`:

```python
async def _should_ingest_video(self, video_info):
    """Filter videos before ingesting"""
    # Check minimum quality thresholds
    if video_info.get('view_count', 0) < 1000:
        return False  # Skip low-quality videos

    # Filter by keywords
    blocked_words = ['spam', 'scam']
    description = video_info.get('description', '').lower()
    if any(word in description for word in blocked_words):
        return False

    return True
```

---

## 📚 Advanced Usage

### Custom Hashtag Scraping

```python
# In your code
from app.tiktok_browser_scraper import TikTokBrowserScraper

async def scrape_custom_hashtags():
    async with TikTokBrowserScraper() as scraper:
        videos = await scraper.scrape_multiple_hashtags(
            hashtags=['yourhashtag1', 'yourhashtag2'],
            videos_per_hashtag=15
        )
        return videos
```

### User Profile Scraping

```python
async def scrape_user_profile(username):
    async with TikTokBrowserScraper() as scraper:
        videos = await scraper.scrape_user_videos(
            username=username,
            limit=30
        )
        return videos
```

### Fallback to Manual URLs

If browser scraping fails, create `backend/app/tiktok_urls.txt`:

```
https://www.tiktok.com/@user/video/123|sports
https://www.tiktok.com/@user/video/456|comedy
https://www.tiktok.com/@user/video/789|music
```

The service will automatically fall back to this list.

---

## 🎉 Summary

### What You Get:

✅ **Automatic TikTok scraping** - No manual work needed
✅ **Browser-based** - Uses real browser, handles JavaScript
✅ **Infinite scroll** - Loads as many videos as you want
✅ **Auto-start** - Begins when you launch platform
✅ **Real-time feeds** - Videos appear immediately
✅ **ML-powered** - Integrated with recommendation engine
✅ **Production-ready** - Error handling, fallbacks, monitoring

### Quick Commands:

```bash
# Start everything
bash START_TIKTOK_PLATFORM.sh

# Check status
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq

# View logs
tail -f backend/logs/app.log

# Access videos
curl http://localhost:8080/api/v1/feed/for-you?user_id=user:test&limit=10 | jq
```

---

## 📖 Related Documentation

- **Browser Scraping Details**: `backend/TIKTOK_BROWSER_SCRAPING.md`
- **Auto-Start Configuration**: `AUTO_START_TIKTOK.md`
- **API Reference**: `http://localhost:8080/docs`
- **Startup Lifecycle**: `docs/STARTUP_LIFECYCLE.md`
- **Real-time Events**: `docs/TIKTOK_REALTIME_GUIDE.md`

---

## 🆘 Support

**Still having issues?**

1. Check the logs: `tail -f backend/logs/app.log`
2. Verify Playwright: `playwright --version`
3. Test scraper: `python -m app.tiktok_browser_scraper`
4. Check API status: `curl localhost:8080/api/v1/tiktok-ingestion/status`

**Everything working?** Videos will appear in your feed every 5 minutes! 🎊
