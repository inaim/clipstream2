# Real Videos Ready for Testing! 🎥

## What's Done

✅ **13 Real Playable Videos** are now configured in `backend/app/initial_videos.py`
✅ **Real Google CDN URLs** - Videos play immediately in browsers
✅ **7 Categories** - sports, comedy, music, gaming, education, food, travel
✅ **Automatic Ingestion** - Videos auto-load when backend starts
✅ **ML Algorithm** - Running and ready to track events
✅ **Event Logging API** - Ready to record swipes/interactions

## Quick Start (3 Steps)

### 1. Start Services

```bash
cd ~/Documents/projects/clipstream
docker-compose up -d surrealdb redis
```

### 2. Start Backend with Real Videos

```bash
cd backend

# Use production videos (real playable URLs)
export INGEST_DEMO_VIDEOS=false
export ENVIRONMENT=development

# Start backend
python3 main.py
```

**You should see:**
```
✅ Phase 3: Ingestion Complete
   - Ingested: 13 videos
   - Skipped: 0 duplicates
   - Categories: sports, comedy, music, gaming, education, food, travel
```

### 3. Test the Videos

```bash
# Get feed with real videos
curl "http://localhost:8080/api/v1/feed/for-you?limit=10" | jq

# You should see real video URLs like:
# "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
```

---

## Test Frontend Swiping + ML

### Create Test User

```bash
USER_ID=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@clipstream.com",
    "password": "test123",
    "display_name": "Test User"
  }' | jq -r '.id')

echo "User ID: $USER_ID"
```

### Get Personalized Feed

```bash
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER_ID&limit=5" | jq
```

### Simulate Swiping Events

**Swipe Up (Like) on sports video:**
```bash
curl -X POST http://localhost:8080/api/v1/events \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"video_id\": \"video:1\",
    \"event_type\": \"like\",
    \"watch_ratio\": 0.8,
    \"category\": \"sports\"
  }"
```

**Swipe Down (Skip) on comedy video:**
```bash
curl -X POST http://localhost:8080/api/v1/events \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"video_id\": \"video:3\",
    \"event_type\": \"skip\",
    \"watch_ratio\": 0.15,
    \"category\": \"comedy\"
  }"
```

**Watch Full Video (Play End):**
```bash
curl -X POST http://localhost:8080/api/v1/events \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"video_id\": \"video:5\",
    \"event_type\": \"play_end\",
    \"watch_ratio\": 0.95,
    \"category\": \"music\"
  }"
```

### See ML Algorithm Adapt

After logging events, fetch feed again:

```bash
curl "http://localhost:8080/api/v1/feed/for-you?user_id=$USER_ID&limit=10" | jq
```

**Expected Result:**
- MORE music/sports videos (you liked these)
- LESS comedy videos (you skipped)
- ML algorithm is optimizing for your preferences!

---

## Verify Events are Recorded

### Check User Analytics

```bash
curl "http://localhost:8080/api/v1/events/analytics/user/$USER_ID" | jq
```

**Shows:**
- Total events
- Category preferences
- Average watch ratios
- Like rates per category

### Check Video Analytics

```bash
curl "http://localhost:8080/api/v1/events/analytics/video/video:1" | jq
```

**Shows:**
- Impressions
- Average watch ratio
- Completion rate
- Like rate
- Skip rate

---

## Frontend Integration

### Video Player Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Clipstream - Swipe Testing</title>
    <style>
        body { margin: 0; font-family: Arial; background: #000; }
        .video-container {
            max-width: 600px;
            margin: 0 auto;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        video {
            width: 100%;
            max-height: 80vh;
            border-radius: 12px;
        }
        .controls {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
        }
        button {
            padding: 15px 30px;
            font-size: 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        .like-btn { background: #ff6b6b; color: white; }
        .skip-btn { background: #4ecdc4; color: white; }
        .next-btn { background: #45b7d1; color: white; }
        .info { color: white; text-align: center; margin: 10px; }
    </style>
</head>
<body>
    <div class="video-container">
        <div class="info" id="video-info"></div>
        <video id="player" controls autoplay></video>
        <div class="controls">
            <button class="like-btn" onclick="likeVideo()">❤️ Like</button>
            <button class="skip-btn" onclick="skipVideo()">⏭️ Skip</button>
            <button class="next-btn" onclick="nextVideo()">➡️ Next</button>
        </div>
        <div class="info" id="stats"></div>
    </div>

    <script>
        const API_URL = 'http://localhost:8080';
        const USER_ID = 'user:1'; // Change this to your user ID

        let videos = [];
        let currentIndex = 0;
        let currentVideo = null;
        let startTime = 0;

        async function loadFeed() {
            const response = await fetch(`${API_URL}/api/v1/feed/for-you?user_id=${USER_ID}&limit=20`);
            videos = await response.json();
            playVideo(0);
        }

        function playVideo(index) {
            if (index >= videos.length) {
                alert('No more videos! Reloading feed...');
                loadFeed();
                return;
            }

            currentIndex = index;
            currentVideo = videos[index];
            startTime = Date.now();

            const player = document.getElementById('player');
            player.src = currentVideo.cdn_url || currentVideo.url;
            player.play();

            document.getElementById('video-info').innerHTML = `
                <h2>${currentVideo.title}</h2>
                <p>Category: ${currentVideo.category} | Video ${index + 1}/${videos.length}</p>
                <p>Score: ${currentVideo.score ? currentVideo.score.toFixed(3) : 'N/A'}</p>
            `;
        }

        async function logEvent(eventType) {
            const player = document.getElementById('player');
            const watchRatio = player.currentTime / player.duration || 0;

            await fetch(`${API_URL}/api/v1/events`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: USER_ID,
                    video_id: currentVideo.id,
                    event_type: eventType,
                    watch_ratio: watchRatio,
                    category: currentVideo.category
                })
            });

            document.getElementById('stats').innerHTML = `
                <p>✅ Logged: ${eventType} (watch ratio: ${(watchRatio * 100).toFixed(0)}%)</p>
            `;
        }

        function likeVideo() {
            logEvent('like');
            setTimeout(() => nextVideo(), 500);
        }

        function skipVideo() {
            logEvent('skip');
            nextVideo();
        }

        function nextVideo() {
            playVideo(currentIndex + 1);
        }

        // Auto-log play_end when video completes
        document.getElementById('player').addEventListener('ended', () => {
            logEvent('play_end');
            nextVideo();
        });

        // Load feed on page load
        loadFeed();
    </script>
</body>
</html>
```

Save as `test_swipe.html` and open in browser!

---

## Complete Testing Flow

### Multi-User Test (Sports Fan vs Comedy Fan)

```bash
# Create Sports Fan
SPORTS_FAN=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"sportsfan@test.com","password":"test123","display_name":"Sports Fan"}' | jq -r '.id')

# Sports Fan likes sports videos
for i in {1..3}; do
  curl -s -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$SPORTS_FAN\",\"video_id\":\"video:$i\",\"event_type\":\"like\",\"watch_ratio\":0.9,\"category\":\"sports\"}"
done

# Create Comedy Fan
COMEDY_FAN=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"comedyfan@test.com","password":"test123","display_name":"Comedy Fan"}' | jq -r '.id')

# Comedy Fan likes comedy videos
for i in {3..5}; do
  curl -s -X POST http://localhost:8080/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$COMEDY_FAN\",\"video_id\":\"video:$i\",\"event_type\":\"like\",\"watch_ratio\":0.9,\"category\":\"comedy\"}"
done

# Compare feeds
echo "=== Sports Fan Feed ==="
curl -s "http://localhost:8080/api/v1/feed/for-you?user_id=$SPORTS_FAN&limit=5" | jq -r '.[] | "\(.title) (\(.category))"'

echo ""
echo "=== Comedy Fan Feed ==="
curl -s "http://localhost:8080/api/v1/feed/for-you?user_id=$COMEDY_FAN&limit=5" | jq -r '.[] | "\(.title) (\(.category))"'
```

**Expected Result:**
- Sports Fan sees MORE sports videos
- Comedy Fan sees MORE comedy videos
- ML algorithm personalizes for each user!

---

## What Happens Now

1. **Backend starts** → Loads 13 real videos into database
2. **Frontend fetches feed** → Gets personalized video list
3. **User swipes** → Frontend calls `/api/v1/events`
4. **Events logged** → Video stats + user preferences updated
5. **ML optimizes** → Next feed fetch shows better recommendations
6. **Repeat** → Algorithm learns in real-time!

---

## Video Categories Available

- **Sports** (2 videos) - Basketball, Soccer
- **Comedy** (2 videos) - Funny Animals, Epic Fails
- **Music** (2 videos) - Guitar Solo, Dance Performance
- **Gaming** (2 videos) - Gaming Highlights, Speedrun
- **Education** (2 videos) - How Things Work, Science Facts
- **Food** (2 videos) - Quick Recipe, Food Review
- **Travel** (1 video) - Travel Vlog

All videos are **real, playable URLs** from Google's public CDN!

---

## Next Steps

1. ✅ Videos are ready - Start backend and test!
2. ✅ Events API is working - Log swipes and interactions
3. ✅ ML algorithm is running - Personalizes feed in real-time
4. 🎯 Connect your frontend - Use the HTML example above
5. 🎯 Test with multiple users - See personalization work
6. 🎯 Add more videos - Replace URLs in `initial_videos.py`

**Everything is wired and ready for testing! 🚀**
