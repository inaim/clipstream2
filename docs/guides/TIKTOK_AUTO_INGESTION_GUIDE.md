# 🎬 TikTok Auto-Ingestion Guide

## What is This?

**Automatic TikTok video ingestion** - A background service that continuously:
- Fetches TikTok videos
- Downloads them with yt-dlp
- Ingests into your database
- Makes them available in your real-time ML feed

---

## Quick Start (3 Steps)

### Step 1: Install yt-dlp

```bash
pip install yt-dlp
# OR
brew install yt-dlp
```

### Step 2: Add TikTok URLs

```bash
# Edit tiktok_urls.txt
nano tiktok_urls.txt

# Add URLs (one per line):
https://www.tiktok.com/@username/video/1234567890|sports
https://www.tiktok.com/@username/video/0987654321|comedy
https://www.tiktok.com/@username/video/5678901234|music
```

### Step 3: Start Auto-Ingestion

```bash
# Start the platform (if not already running)
bash START_TIKTOK_PLATFORM.sh

# Start auto-ingestion via API
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" | jq
```

**That's it!** Videos will be fetched and ingested every 5 minutes.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│              TIKTOK AUTO-INGESTION FLOW                      │
└─────────────────────────────────────────────────────────────┘

Every 5 minutes:
    ↓
Read tiktok_urls.txt
    ↓
For each URL:
    ↓
  Download with yt-dlp
    ↓
  Extract metadata (title, creator, views, etc.)
    ↓
  Save video file
    ↓
  Insert into SurrealDB
    ↓
Video available in feed!
    ↓
ML ranks it with your preferences
    ↓
You see it in the swipe interface
```

**End-to-end:** ~30 seconds per video

---

## API Endpoints

### Start Auto-Ingestion

```bash
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -H "Content-Type: application/json" \
     -d '{
       "fetch_interval": 300,
       "videos_per_fetch": 10
     }' | jq
```

**Response:**
```json
{
  "success": true,
  "message": "TikTok auto-ingestion started",
  "status": {
    "is_running": true,
    "fetch_interval": 300,
    "videos_per_fetch": 10,
    "total_fetched": 0,
    "total_ingested": 0,
    "total_failed": 0
  }
}
```

### Stop Auto-Ingestion

```bash
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/stop" | jq
```

### Check Status

```bash
curl "http://localhost:8080/api/v1/tiktok-ingestion/status" | jq
```

**Response:**
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "fetch_interval": 300,
    "videos_per_fetch": 10,
    "total_fetched": 25,
    "total_ingested": 23,
    "total_failed": 2,
    "success_rate": 0.92,
    "last_fetch_time": 1703001234.56
  }
}
```

### Trigger Manual Ingestion

```bash
# Force an ingestion cycle immediately (don't wait 5 minutes)
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/trigger-now" | jq
```

---

## Configuration

### Fetch Interval

How often to check for new videos:

```bash
# Every 5 minutes (default)
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"fetch_interval": 300}' | jq

# Every 10 minutes
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"fetch_interval": 600}' | jq

# Every 1 hour
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"fetch_interval": 3600}' | jq
```

### Videos Per Fetch

How many videos to process per cycle:

```bash
# Process 10 videos per cycle (default)
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"videos_per_fetch": 10}' | jq

# Process 50 videos per cycle
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"videos_per_fetch": 50}' | jq
```

---

## Adding TikTok URLs

### Method 1: Edit tiktok_urls.txt (Easiest)

```bash
# Edit the file
nano tiktok_urls.txt

# Add URLs:
https://www.tiktok.com/@user/video/123|sports
https://www.tiktok.com/@user/video/456|comedy
https://www.tiktok.com/@user/video/789|music

# Save and exit
# Auto-ingestion will pick them up on next cycle
```

### Method 2: Programmatically Add URLs

```python
# Python script to add URLs
import asyncio

urls_to_add = [
    "https://www.tiktok.com/@user/video/123|sports",
    "https://www.tiktok.com/@user/video/456|comedy",
]

with open("tiktok_urls.txt", "a") as f:
    for url in urls_to_add:
        f.write(url + "\n")

print(f"Added {len(urls_to_add)} URLs")
```

### Method 3: Use TikTok API (Advanced)

If you have TikTok API access:

```python
# backend/app/tiktok_auto_ingestion.py
# Modify _get_trending_tiktok_urls() method:

from TikTokApi import TikTokApi

async def _get_trending_tiktok_urls(self):
    async with TikTokApi() as api:
        trending = api.trending.videos(count=self.videos_per_fetch)

        urls = []
        async for video in trending:
            urls.append({
                "url": video.video.downloadAddr,
                "category": "trending"
            })

        return urls
```

---

## Troubleshooting

### "yt-dlp not installed"

```bash
pip install yt-dlp
# OR
brew install yt-dlp

# Verify installation
yt-dlp --version
```

### "No TikTok URLs found"

Make sure `tiktok_urls.txt` exists and has URLs:

```bash
# Check file exists
ls -la tiktok_urls.txt

# Check content
cat tiktok_urls.txt

# Add sample URL
echo "https://www.tiktok.com/@user/video/123|sports" >> tiktok_urls.txt
```

### "Download failed"

Common causes:
- Invalid TikTok URL
- Video deleted/private
- TikTok rate limiting
- Network issues

Check logs:
```bash
# Check backend logs
tail -f backend/logs/app.log

# Or run with verbose logging
LOGGING_LEVEL=DEBUG bash START_TIKTOK_PLATFORM.sh
```

### "Videos not appearing in feed"

1. **Check ingestion status:**
```bash
curl "http://localhost:8080/api/v1/tiktok-ingestion/status" | jq
```

2. **Check database:**
```bash
# Query videos in database
curl "http://localhost:8080/api/v1/videos" | jq '.videos | length'
```

3. **Trigger manual refresh:**
```bash
curl -X POST "http://localhost:8080/api/v1/infinite/refresh" | jq
```

---

## Production Deployment

### Automatic Startup

Add to your startup script:

```bash
# In START_TIKTOK_PLATFORM.sh
# After backend starts, enable auto-ingestion

sleep 5  # Wait for backend to be ready

curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"fetch_interval": 300}' > /dev/null 2>&1

echo "✅ TikTok auto-ingestion enabled"
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/tiktok-ingestion.service

[Unit]
Description=TikTok Auto-Ingestion Service
After=network.target

[Service]
Type=simple
User=clipstream
WorkingDirectory=/opt/clipstream
ExecStart=/usr/bin/curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Docker Integration

```yaml
# docker-compose.yml

services:
  backend:
    # ... existing config
    environment:
      - TIKTOK_AUTO_INGESTION=true
      - TIKTOK_FETCH_INTERVAL=300
      - TIKTOK_VIDEOS_PER_FETCH=10
```

### Health Monitoring

```bash
# Check if ingestion is running
status=$(curl -s "http://localhost:8080/api/v1/tiktok-ingestion/status" | jq -r '.status.is_running')

if [ "$status" != "true" ]; then
    echo "⚠️  Auto-ingestion not running! Starting..."
    curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start"
fi
```

---

## Performance

### Ingestion Speed

- **Download:** ~5-10 seconds per video (depends on size)
- **Metadata extraction:** ~1 second
- **Database insertion:** ~0.1 seconds
- **Total:** ~10 seconds per video

### Resource Usage

- **CPU:** Minimal (yt-dlp is efficient)
- **Memory:** ~100 MB per video (temporary)
- **Disk:** Depends on video length (1-5 MB per minute)
- **Network:** ~2-5 MB per video

### Scaling

**For high volume (100+ videos/hour):**

1. **Increase fetch interval:**
```bash
curl -X POST "http://localhost:8080/api/v1/tiktok-ingestion/start" \
     -d '{"fetch_interval": 60, "videos_per_fetch": 50}'
```

2. **Use multiple workers:**
```python
# Run multiple ingestion services in parallel
workers = 3
for i in range(workers):
    service = TikTokAutoIngestion()
    await service.start()
```

3. **Use distributed task queue:**
```python
# Use Celery for distributed ingestion
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def ingest_tiktok_video(url):
    # Download and ingest
    pass
```

---

## Legal Considerations

**⚠️ IMPORTANT:**

1. **TikTok Terms of Service:**
   - Downloading TikTok videos may violate TikTok's TOS
   - Use only for educational/testing purposes
   - Don't redistribute or monetize downloaded content

2. **Copyright:**
   - Videos belong to their creators
   - Respect copyright laws
   - Get permission before using

3. **Best Practices:**
   - Use for personal testing only
   - Consider user-generated content instead
   - Partner with creators for licensed content
   - Use Creative Commons videos

---

## Alternatives to TikTok Scraping

### 1. User-Generated Content (Recommended)

Let users upload their own videos:

```bash
curl -X POST "http://localhost:8080/api/v1/videos/upload" \
     -F "file=@video.mp4" \
     -F "category=comedy"
```

**Benefits:**
- No copyright issues
- No TOS violations
- Users control content
- Builds community

### 2. Licensed Content

Partner with content creators:

- Stock video sites (Pexels, Pixabay)
- Creator partnerships
- Licensed video libraries
- Creative Commons content

### 3. TikTok Official API

Apply for TikTok API access:

- https://developers.tiktok.com/
- Requires approval
- Official and legal
- Access to trending feed

---

## Summary

**Auto-ingestion is now working!**

✅ Background service runs every 5 minutes
✅ Fetches TikTok URLs from `tiktok_urls.txt`
✅ Downloads with yt-dlp
✅ Ingests into database
✅ Appears in your real-time ML feed

**To start using:**

1. Install yt-dlp: `pip install yt-dlp`
2. Add URLs: Edit `tiktok_urls.txt`
3. Start service: `curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start`
4. Watch videos appear in feed!

**Your platform now has continuous TikTok video ingestion! 🎉**