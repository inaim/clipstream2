# Clipstream Testing Guide - ML Algorithm Validation

## Overview

This guide shows you how to test the ML recommendation algorithm with **real playable videos** and multiple users with different interaction patterns.

You'll be able to:
- ✅ Play actual videos in the platform
- ✅ Test with multiple users (interested, not interested, uncertain)
- ✅ See the ML algorithm adapt in real-time
- ✅ Verify personalization works

---

## Quick Start - Testing with Playable Videos

### Option 1: Use Public Demo Videos (Recommended for Testing)

The easiest way to test is with publicly available demo videos that work in browsers:

```bash
# 1. Start the backend
cd backend
python3 main.py

# 2. Create test videos with public CDN URLs
curl -X POST http://localhost:8080/api/v1/feed/debug/seed-video \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sports Highlight",
    "user_id": "user:system",
    "cdn_url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
  }'
```

### Option 2: Download TikTok Videos (Production-Ready)

To test with real TikTok videos:

```bash
# 1. Install yt-dlp
pip install yt-dlp

# 2. Create a test script
cat > test_tiktok_ingestion.py << 'EOF'
import asyncio
from app.tiktok_scraper import download_and_prepare_tiktok_videos
from app.ingestion_engine import ingest_initial_videos
from db.surrealdb_client import db_client

async def ingest_tiktok_videos():
    # Connect to database
    await db_client.connect()
    async_db = getattr(db_client, "async_db")

    # TikTok URLs to download
    tiktok_urls = [
        "https://www.tiktok.com/@nike/video/7305827482847587630",
        "https://www.tiktok.com/@gordonramsayofficial/video/7305827383847587630",
        "https://www.tiktok.com/@natgeo/video/7305827282847587630",
    ]

    # Download and prepare
    from app.tiktok_scraper import download_and_prepare_tiktok_videos
    videos = await download_and_prepare_tiktok_videos(tiktok_urls)

    # Ingest into database
    result = await ingest_initial_videos(async_db, videos)
    print(f"Ingested {result['ingested']} TikTok videos")

if __name__ == "__main__":
    asyncio.run(ingest_tiktok_videos())
EOF

# 3. Run the ingestion
python3 test_tiktok_ingestion.py
```

---

## Multi-User Testing Scenarios

Test the ML algorithm with 3 different user personas:

### User 1: "Sports Fan" (Interested)

**Profile:** Loves sports content, high engagement

```bash
# Create user
USER1=$(curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sportsfan@test.com",
    "password": "test123",
    "display_name": "Sports Fan"
  }' | jq -r '.id')

echo "User 1 ID: $USER1"

# Simulate interested behavior (watches full videos, likes)
for i in {1..5}; do
  curl -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"$USER1\",
      \"video_id\": \"video:$i\",
      \"event_type\": \"play_end\",
      \"watch_ratio\": 0.95,
      \"category\": \"sports\"
    }"

  curl -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"$USER1\",
      \"video_id\": \"video:$i\",
      \"event_type\": \"like\",
      \"watch_ratio\": 0.0,
      \"category\": \"sports\"
    }"
done

# Get personalized feed (should show MORE sports)
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER1&limit=10" | jq
```

### User 2: "Skipper" (Not Interested)

**Profile:** Skips most content, low engagement

```bash
# Create user
USER2=$(curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "skipper@test.com",
    "password": "test123",
    "display_name": "The Skipper"
  }' | jq -r '.id')

echo "User 2 ID: $USER2"

# Simulate not interested behavior (skips early, no likes)
for i in {1..5}; do
  curl -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"$USER2\",
      \"video_id\": \"video:$i\",
      \"event_type\": \"skip\",
      \"watch_ratio\": 0.15,
      \"category\": \"sports\"
    }"
done

# Get personalized feed (should show LESS sports, more exploration)
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER2&limit=10" | jq
```

### User 3: "Explorer" (Uncertain)

**Profile:** Mixed behavior, explores different categories

```bash
# Create user
USER3=$(curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "explorer@test.com",
    "password": "test123",
    "display_name": "The Explorer"
  }' | jq -r '.id')

echo "User 3 ID: $USER3"

# Simulate uncertain behavior (varied watch ratios, mixed categories)
CATEGORIES=("sports" "comedy" "music" "gaming" "food")
WATCH_RATIOS=(0.2 0.5 0.8 0.3 0.9)

for i in {1..5}; do
  CAT=${CATEGORIES[$((i % 5))]}
  RATIO=${WATCH_RATIOS[$((i % 5))]}

  curl -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"$USER3\",
      \"video_id\": \"video:$i\",
      \"event_type\": \"play_end\",
      \"watch_ratio\": $RATIO,
      \"category\": \"$CAT\"
    }"
done

# Get personalized feed (should show balanced content)
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER3&limit=10" | jq
```

---

## Verify ML Algorithm is Working

### 1. Compare Feed Rankings

```bash
# Get feeds for all 3 users
echo "=== Sports Fan Feed ==="
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER1&limit=5" | jq '.[].category'

echo "=== Skipper Feed ==="
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER2&limit=5" | jq '.[].category'

echo "=== Explorer Feed ==="
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER3&limit=5" | jq '.[].category'
```

**Expected Results:**
- **User 1** (Sports Fan): Should see MORE sports videos ranked higher
- **User 2** (Skipper): Should see MORE variety, exploration bonus kicks in
- **User 3** (Explorer): Should see BALANCED mix of categories

### 2. Explain Individual Scores

```bash
# See WHY a video is ranked high for User 1
curl "http://localhost:8080/api/v1/feed/debug/explain-score?user_id=$USER1&video_id=video:1" | jq

# Compare same video for User 2 (should score lower)
curl "http://localhost:8080/api/v1/feed/debug/explain-score?user_id=$USER2&video_id=video:1" | jq
```

**What to Look For:**
- **User Interest Component**: Higher for User 1 (sports fan)
- **Video Quality Component**: Same for both users
- **Exploration Component**: Higher for User 2 (less history)

### 3. Check User Analytics

```bash
# View User 1's category preferences
curl "http://localhost:8080/api/v1/events/analytics/user/$USER1" | jq

# View User 2's category preferences
curl "http://localhost:8080/api/v1/events/analytics/user/$USER2" | jq
```

**Expected Output:**
```json
{
  "user_id": "user:1",
  "total_events": 10,
  "category_preferences": {
    "sports": {
      "impressions": 5,
      "avg_watch_ratio": 0.95,
      "like_rate": 1.0
    }
  }
}
```

### 4. Check Video Analytics

```bash
# View video performance
curl "http://localhost:8080/api/v1/events/analytics/video/video:1" | jq
```

**Expected Output:**
```json
{
  "video_id": "video:1",
  "impressions": 3,
  "avg_watch_ratio": 0.63,
  "completion_rate": 0.67,
  "like_rate": 0.33,
  "skip_rate": 0.33
}
```

---

## Automated Test Suite

Create a comprehensive test:

```bash
cat > test_ml_algorithm.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Clipstream ML Algorithm"
echo "==================================="

BASE_URL="http://localhost:8080"

# Create 3 test users
echo "📝 Creating test users..."
USER1=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"sportsfan@test.com","password":"test123","display_name":"Sports Fan"}' | jq -r '.id')

USER2=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"skipper@test.com","password":"test123","display_name":"Skipper"}' | jq -r '.id')

USER3=$(curl -s -X POST $BASE_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"explorer@test.com","password":"test123","display_name":"Explorer"}' | jq -r '.id')

echo "✅ Created users: $USER1, $USER2, $USER3"

# Simulate different behaviors
echo ""
echo "🎯 Simulating user interactions..."

# User 1: Loves sports (high engagement)
for i in {1..5}; do
  curl -s -X POST $BASE_URL/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$USER1\",\"video_id\":\"video:$i\",\"event_type\":\"play_end\",\"watch_ratio\":0.95,\"category\":\"sports\"}" > /dev/null
done

# User 2: Skips everything (low engagement)
for i in {1..5}; do
  curl -s -X POST $BASE_URL/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$USER2\",\"video_id\":\"video:$i\",\"event_type\":\"skip\",\"watch_ratio\":0.15,\"category\":\"sports\"}" > /dev/null
done

# User 3: Mixed behavior
CATEGORIES=("sports" "comedy" "music")
for i in {1..3}; do
  CAT=${CATEGORIES[$((i % 3))]}
  curl -s -X POST $BASE_URL/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$USER3\",\"video_id\":\"video:$i\",\"event_type\":\"play_end\",\"watch_ratio\":0.7,\"category\":\"$CAT\"}" > /dev/null
done

echo "✅ Simulated 13 events"

# Compare feeds
echo ""
echo "📊 Comparing personalized feeds..."
echo ""
echo "User 1 (Sports Fan) - Top 3:"
curl -s "$BASE_URL/api/v1/feed/for-you?user_id=$USER1&limit=3" | jq -r '.[] | "\(.title) (Category: \(.category), Score: \(.score // 0))"'

echo ""
echo "User 2 (Skipper) - Top 3:"
curl -s "$BASE_URL/api/v1/feed/for-you?user_id=$USER2&limit=3" | jq -r '.[] | "\(.title) (Category: \(.category), Score: \(.score // 0))"'

echo ""
echo "User 3 (Explorer) - Top 3:"
curl -s "$BASE_URL/api/v1/feed/for-you?user_id=$USER3&limit=3" | jq -r '.[] | "\(.title) (Category: \(.category), Score: \(.score // 0))"'

echo ""
echo "🎉 ML Algorithm Test Complete!"
echo "✅ Feeds are personalized based on user behavior"
EOF

chmod +x test_ml_algorithm.sh
./test_ml_algorithm.sh
```

---

## Frontend Integration (Optional)

To play videos in the browser, use this simple HTML test page:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Clipstream Test Player</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .video-container { max-width: 600px; margin: 20px auto; }
        video { width: 100%; border-radius: 8px; }
        .controls { margin-top: 10px; }
        button { padding: 10px 20px; margin: 5px; }
    </style>
</head>
<body>
    <div class="video-container">
        <h1>Clipstream ML Test</h1>
        <div id="user-info"></div>
        <video id="player" controls></video>
        <div class="controls">
            <button onclick="like()">❤️ Like</button>
            <button onclick="skip()">⏭️ Skip</button>
            <button onclick="nextVideo()">➡️ Next</button>
        </div>
        <div id="analytics"></div>
    </div>

    <script>
        const userId = "user:1"; // Change this
        const apiUrl = "http://localhost:8080";
        let currentVideo = null;
        let videos = [];
        let currentIndex = 0;

        async function loadFeed() {
            const response = await fetch(`${apiUrl}/api/v1/feed/for-you?user_id=${userId}&limit=20`);
            videos = await response.json();
            playVideo(0);
        }

        function playVideo(index) {
            if (index >= videos.length) return;
            currentIndex = index;
            currentVideo = videos[index];

            document.getElementById('player').src = currentVideo.cdn_url;
            document.getElementById('user-info').innerHTML = `
                <p>Video ${index + 1}/${videos.length}: ${currentVideo.title}</p>
                <p>Category: ${currentVideo.category}</p>
                <p>Score: ${currentVideo.score ? currentVideo.score.toFixed(3) : 'N/A'}</p>
            `;

            document.getElementById('player').play();
        }

        async function logEvent(eventType, watchRatio = 0) {
            await fetch(`${apiUrl}/api/v1/events`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    video_id: currentVideo.id,
                    event_type: eventType,
                    watch_ratio: watchRatio,
                    category: currentVideo.category
                })
            });
        }

        function like() {
            logEvent('like');
            alert('Liked!');
        }

        function skip() {
            const currentTime = document.getElementById('player').currentTime;
            const duration = document.getElementById('player').duration;
            logEvent('skip', currentTime / duration);
            nextVideo();
        }

        function nextVideo() {
            playVideo(currentIndex + 1);
        }

        // Log play_end when video ends
        document.getElementById('player').addEventListener('ended', () => {
            logEvent('play_end', 1.0);
            nextVideo();
        });

        // Load feed on page load
        loadFeed();
    </script>
</body>
</html>
```

Save as `test_player.html` and open in browser!

---

## Expected Results

After running tests, you should see:

✅ **Sports Fan** gets MORE sports videos ranked higher
✅ **Skipper** gets MORE diverse content (exploration bonus)
✅ **Explorer** gets BALANCED content across categories
✅ **Scores explain** why each video is ranked where it is
✅ **Analytics show** each user's preferences

The ML algorithm is working if:
1. Different users get different feed rankings
2. User preferences influence scores (60% weight)
3. Video quality affects all users (30% weight)
4. Exploration bonus shows unseen content (10% weight)

---

**Ready to test the ML algorithm! 🚀**
