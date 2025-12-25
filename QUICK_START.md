# Quick Start - Get Real Videos Playing NOW

## Problem
You need **real playable videos** in the platform to test swiping and see the ML algorithm work.

## Solution - 2 Minute Setup

### Step 1: Update Initial Videos (Use Real URLs)

Edit `backend/app/initial_videos.py` and replace the PRODUCTION_VIDEOS list with these REAL playable videos:

```python
# REAL PLAYABLE VIDEOS - These work in browsers!
PRODUCTION_VIDEOS = [
    {
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "category": "sports",
        "duration": 596.5,
        "title": "Basketball Highlights",
        "tags": ["sports", "basketball"],
        "creator_id": "user:system",
        "embedding": [],
    },
    {
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "category": "comedy",
        "duration": 15.0,
        "title": "Funny Animals",
        "tags": ["comedy", "funny"],
        "creator_id": "user:system",
        "embedding": [],
    },
    {
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "category": "music",
        "duration": 60.0,
        "title": "Guitar Solo",
        "tags": ["music", "guitar"],
        "creator_id": "user:system",
        "embedding": [],
    },
    {
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
        "category": "gaming",
        "duration": 15.0,
        "title": "Gaming Highlights",
        "tags": ["gaming", "esports"],
        "creator_id": "user:system",
        "embedding": [],
    },
]
```

### Step 2: Start Backend with Production Videos

```bash
cd ~/Documents/projects/clipstream

# Start services
docker-compose up -d surrealdb redis

# Start backend with PRODUCTION videos (not demo)
cd backend
INGEST_DEMO_VIDEOS=false python3 main.py
```

### Step 3: Add Production Videos to Database

In another terminal:

```bash
cd ~/Documents/projects/clipstream/backend

python3 << 'EOF'
import asyncio
from app.startup import init_surreal
from app.ingestion_engine import ingest_initial_videos
from app.initial_videos import PRODUCTION_VIDEOS
from utils.config import settings

async def main():
    db = await init_surreal(
        db_url=settings.SURREALDB_URL,
        user=settings.SURREALDB_USER,
        password=settings.SURREALDB_PASS,
        namespace=settings.SURREALDB_NS,
        database=settings.SURREALDB_DB
    )
    result = await ingest_initial_videos(db, PRODUCTION_VIDEOS)
    print(f"✅ Added {result['ingested']} videos!")

asyncio.run(main())
EOF
```

### Step 4: Verify Videos are There

```bash
curl http://localhost:8080/api/v1/feed/for-you?limit=10 | jq '.[].title'
```

You should see:
```
"Basketball Highlights"
"Funny Animals"
"Guitar Solo"
"Gaming Highlights"
```

### Step 5: Test in Frontend

Your frontend can now:
1. Fetch videos from `/api/v1/feed/for-you`
2. Play them in a `<video>` tag
3. Log events when users swipe

```javascript
// In your React Native or React app:
const response = await fetch('http://localhost:8080/api/v1/feed/for-you?limit=20');
const videos = await response.json();

// Play first video
<video src={videos[0].cdn_url} controls />

// When user swipes/likes:
await fetch('http://localhost:8080/api/v1/events', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user:1',
    video_id: videos[0].id,
    event_type: 'like',
    watch_ratio: 0.75,
    category: videos[0].category
  })
});
```

## Test the ML Algorithm

Create 3 test users with different behaviors:

```bash
# User 1: Loves sports
for i in {1..5}; do
  curl -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d '{"user_id":"user:1","video_id":"video:1","event_type":"like","watch_ratio":0.9,"category":"sports"}'
done

# User 2: Hates sports
for i in {1..5}; do
  curl -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d '{"user_id":"user:2","video_id":"video:1","event_type":"skip","watch_ratio":0.1,"category":"sports"}'
done

# Compare feeds
echo "User 1 (sports fan):"
curl -s "http://localhost:8080/api/v1/feed/for-you?user_id=user:1&limit=3" | jq '.[].category'

echo "User 2 (not interested):"
curl -s "http://localhost:8080/api/v1/feed/for-you?user_id=user:2&limit=3" | jq '.[].category'
```

**User 1 should get MORE sports, User 2 should get LESS sports!**

## Done! 🎉

You now have:
- ✅ Real playable videos in the platform
- ✅ ML algorithm learning from swipes
- ✅ Different users getting different feeds
- ✅ Ready to test in frontend!
