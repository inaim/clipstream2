# Complete Setup Guide - TikTok Auto-Ingestion

## ✅ YES! START_TIKTOK_PLATFORM.sh is the Correct Script

I've updated `START_TIKTOK_PLATFORM.sh` to automatically enable TikTok video ingestion!

## 🚀 What Happens When You Run It

```bash
bash START_TIKTOK_PLATFORM.sh
```

### Step-by-Step:

1. ✅ **Starts Docker services**
   - SurrealDB (database)
   - Redis (caching/events)

2. ✅ **Checks dependencies**
   - yt-dlp (video downloader)
   - Playwright (browser automation)
   - Auto-installs if missing!

3. ✅ **Sets environment variables**
   - `ENABLE_TIKTOK_AUTO_INGEST=true` ← **NEW!**
   - `INGEST_DEMO_VIDEOS=false`
   - Development mode

4. ✅ **Starts backend with auto-ingestion**
   - Backend launches on port 8080
   - TikTok scraper auto-starts
   - Videos pulled every 5 minutes

5. ✅ **Videos appear in frontend automatically**
   - Feed endpoint: `/api/v1/feed/for-you`
   - Infinite scroll: `/api/v1/infinite/feed`
   - Real-time updates via SSE

---

## 📺 What You'll See

### In the Terminal:
```
🚀 Starting Clipstream - TikTok-Style Platform
==============================================

✓ Docker is running
✓ SurrealDB is ready on port 8000
✓ Redis is ready on port 6379
✓ yt-dlp is installed
✓ Environment configured
✓ TikTok auto-ingestion ENABLED

🎬 Starting backend with real-time ML + TikTok Auto-Ingestion...

Backend will start with:
  - TikTok Auto-Ingestion (browser scraping every 5 minutes) 🤖
  - Infinite scroll feed
  - Real-time ML feedback (SSE)
  - Event buffering

📺 TikTok videos will appear in your feed automatically!
   - Sources: #fyp, #viral, #trending, etc.
   - Scraping interval: 5 minutes
   - Videos per cycle: 10

🌐 Access your dashboard at:
   - Backend API: http://localhost:8080
   - Health check: http://localhost:8080/health
   - API docs: http://localhost:8080/docs
```

### In the Backend Logs:
```
[STEP 3.5] Starting TikTok auto-ingestion with browser scraping...
✅ TikTok auto-ingestion service started (browser scraping enabled)
   - Scraping trending hashtags every 5 minutes
   - Browser: Headless Chromium with infinite scroll
   - Sources: #fyp, #viral, #trending, etc.

[STEP 4] Platform ready for beta
```

---

## 🎯 How Videos Reach Your Frontend

### Flow:

```
START_TIKTOK_PLATFORM.sh runs
         ↓
Backend starts (main.py)
         ↓
Auto-ingestion starts (line 142 in main.py)
         ↓
Every 5 minutes:
         ↓
Browser scrapes TikTok → Downloads videos → Stores in DB
         ↓
Videos available at API endpoints:
  - /api/v1/feed/for-you?user_id=...
  - /api/v1/infinite/feed
         ↓
Your frontend calls these endpoints
         ↓
Videos appear in user dashboard! 🎉
```

---

## 🌐 Frontend Integration

### Option 1: React/Next.js Frontend

```javascript
// Fetch videos for user feed
const response = await fetch('http://localhost:8080/api/v1/feed/for-you?user_id=user:123&limit=20');
const data = await response.json();
const videos = data.videos;

// Display in your dashboard
videos.map(video => (
  <VideoCard
    key={video.id}
    url={video.cdn_url}
    title={video.title}
    creator={video.creator_name}
  />
));
```

### Option 2: Infinite Scroll Feed

```javascript
// Cursor-based pagination
const response = await fetch('http://localhost:8080/api/v1/infinite/feed?limit=10');
const { videos, next_cursor } = await response.json();

// Load more when user scrolls
const loadMore = async () => {
  const response = await fetch(`http://localhost:8080/api/v1/infinite/feed?cursor=${next_cursor}`);
  // ... append videos
};
```

### Option 3: Real-time Updates (SSE)

```javascript
// Listen for new videos in real-time
const eventSource = new EventSource('http://localhost:8080/api/videos/events/global');

eventSource.addEventListener('video_created', (event) => {
  const newVideo = JSON.parse(event.data);
  console.log('New TikTok video ingested:', newVideo);
  // Add to feed UI
});
```

---

## 📊 Monitoring Auto-Ingestion

### Check Status:
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
    "success_rate": 0.933
  }
}
```

### Trigger Manual Fetch:
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/trigger-now | jq
```

---

## 🛠️ Configuration

### Change Scraping Frequency

Edit `backend/app/tiktok_auto_ingestion.py`:
```python
FETCH_INTERVAL = 180  # 3 minutes instead of 5
VIDEOS_PER_FETCH = 20  # 20 videos instead of 10
```

Or configure via API:
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{"fetch_interval": 180, "videos_per_fetch": 20}'
```

### Change Hashtags

Edit `backend/app/tiktok_auto_ingestion.py`:
```python
TRENDING_HASHTAGS = [
    "fyp", "foryou", "viral", "trending",
    "yourhashtag1", "yourhashtag2"
]
```

---

## 🎨 Frontend Example (Complete)

Here's a complete example of displaying videos:

```tsx
// components/VideoFeed.tsx
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

export default function VideoFeed({ userId }: { userId: string }) {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
    // Refresh every minute to get new videos
    const interval = setInterval(fetchVideos, 60000);
    return () => clearInterval(interval);
  }, [userId]);

  const fetchVideos = async () => {
    try {
      const res = await fetch(`http://localhost:8080/api/v1/feed/for-you?user_id=${userId}&limit=20`);
      const data = await res.json();
      setVideos(data.videos || []);
    } catch (error) {
      console.error('Failed to fetch videos:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading TikTok videos...</div>;

  return (
    <div className="video-feed">
      {videos.map(video => (
        <div key={video.id} className="video-card">
          <video src={video.cdn_url} controls />
          <h3>{video.title}</h3>
          <p>@{video.creator_name}</p>
          <div className="stats">
            <span>👁️ {video.view_count}</span>
            <span>❤️ {video.like_count}</span>
          </div>
          <div className="hashtags">
            {video.hashtags.map(tag => (
              <span key={tag}>#{tag}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## ✅ Complete Setup Checklist

- [ ] Run `bash START_TIKTOK_PLATFORM.sh`
- [ ] Wait for backend to start
- [ ] Verify auto-ingestion started (check logs)
- [ ] Wait 5 minutes for first batch of videos
- [ ] Check API: `curl http://localhost:8080/api/v1/feed/for-you?user_id=user:test&limit=10`
- [ ] See videos in response
- [ ] Connect frontend to API endpoints
- [ ] Videos appear in user dashboard! 🎉

---

## 🎉 Summary

**YES!** `START_TIKTOK_PLATFORM.sh` is the **correct script** to:

1. ✅ Start all services (database, cache, backend)
2. ✅ Enable TikTok auto-ingestion automatically
3. ✅ Pull videos every 5 minutes via browser scraping
4. ✅ Make videos available at API endpoints
5. ✅ Your frontend fetches and displays them

**Just run it and videos will flow automatically!** 🚀

```bash
bash START_TIKTOK_PLATFORM.sh
```

Then your frontend can fetch from:
- `http://localhost:8080/api/v1/feed/for-you`
- `http://localhost:8080/api/v1/infinite/feed`

Videos will appear in your user dashboard automatically! 🎊
