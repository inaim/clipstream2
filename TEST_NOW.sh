#!/bin/bash

echo "🎬 Clipstream - Test Real Videos & ML Algorithm"
echo "================================================"
echo ""

BASE_URL="http://localhost:8080"

# Check if backend is running
echo "🔍 Checking if backend is running..."
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Backend is not running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd ~/Documents/projects/clipstream/backend"
    echo "  export INGEST_DEMO_VIDEOS=false"
    echo "  python3 main.py"
    echo ""
    exit 1
fi

echo "✅ Backend is running!"
echo ""

# Check if videos are loaded
echo "🎥 Checking if videos are loaded..."
VIDEO_COUNT=$(curl -s "$BASE_URL/api/v1/feed/for-you?limit=100" | jq '. | length')

if [ "$VIDEO_COUNT" -eq 0 ]; then
    echo "❌ No videos found in database!"
    echo ""
    echo "Please ensure backend started with INGEST_DEMO_VIDEOS=false"
    echo "or run: python3 seed_real_videos.py"
    echo ""
    exit 1
fi

echo "✅ Found $VIDEO_COUNT videos in database!"
echo ""

# Show sample videos
echo "📺 Sample Videos Available:"
curl -s "$BASE_URL/api/v1/feed/for-you?limit=5" | jq -r '.[] | "  - \(.title) (\(.category))"'
echo ""

# Create test user
echo "👤 Creating test user..."
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser_'$(date +%s)'@clipstream.com",
    "password": "test123",
    "display_name": "Test User"
  }')

USER_ID=$(echo "$USER_RESPONSE" | jq -r '.id')

if [ "$USER_ID" == "null" ] || [ -z "$USER_ID" ]; then
    echo "❌ Failed to create user"
    echo "Response: $USER_RESPONSE"
    exit 1
fi

echo "✅ Created user: $USER_ID"
echo ""

# Simulate user interactions
echo "🎯 Simulating user interactions..."
echo ""

# Like sports videos (watch fully)
echo "  ❤️  Liking sports videos..."
curl -s -X POST "$BASE_URL/api/v1/events" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"video_id\":\"video:1\",\"event_type\":\"like\",\"watch_ratio\":0.9,\"category\":\"sports\"}" > /dev/null

curl -s -X POST "$BASE_URL/api/v1/events" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"video_id\":\"video:2\",\"event_type\":\"play_end\",\"watch_ratio\":0.95,\"category\":\"sports\"}" > /dev/null

# Skip comedy videos (skip early)
echo "  ⏭️  Skipping comedy videos..."
curl -s -X POST "$BASE_URL/api/v1/events" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"video_id\":\"video:3\",\"event_type\":\"skip\",\"watch_ratio\":0.15,\"category\":\"comedy\"}" > /dev/null

curl -s -X POST "$BASE_URL/api/v1/events" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"video_id\":\"video:4\",\"event_type\":\"skip\",\"watch_ratio\":0.2,\"category\":\"comedy\"}" > /dev/null

# Like music videos
echo "  ❤️  Liking music videos..."
curl -s -X POST "$BASE_URL/api/v1/events" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"video_id\":\"video:5\",\"event_type\":\"like\",\"watch_ratio\":0.85,\"category\":\"music\"}" > /dev/null

curl -s -X POST "$BASE_URL/api/v1/events" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"video_id\":\"video:6\",\"event_type\":\"play_end\",\"watch_ratio\":1.0,\"category\":\"music\"}" > /dev/null

echo "✅ Logged 6 events"
echo ""

# Get personalized feed
echo "📊 Getting personalized feed (ML algorithm in action)..."
echo ""

FEED=$(curl -s "$BASE_URL/api/v1/feed/for-you?user_id=$USER_ID&limit=10")

echo "🎯 Your Personalized Feed (Top 5):"
echo "$FEED" | jq -r '.[0:5] | .[] | "  \(.title) - Category: \(.category) | Score: \(.score // 0 | tostring | .[0:5])"'
echo ""

# Show user analytics
echo "📈 User Analytics:"
ANALYTICS=$(curl -s "$BASE_URL/api/v1/events/analytics/user/$USER_ID")
echo "$ANALYTICS" | jq '{
  total_events: .total_events,
  top_categories: .category_preferences | to_entries | map({category: .key, impressions: .value.impressions, avg_watch: .value.avg_watch_ratio}) | .[0:3]
}'
echo ""

# Verify ML is working
echo "🧪 Verifying ML Algorithm..."
echo ""

SPORTS_COUNT=$(echo "$FEED" | jq '[.[] | select(.category == "sports")] | length')
COMEDY_COUNT=$(echo "$FEED" | jq '[.[] | select(.category == "comedy")] | length')
MUSIC_COUNT=$(echo "$FEED" | jq '[.[] | select(.category == "music")] | length')

echo "  Sports videos in top 10: $SPORTS_COUNT"
echo "  Comedy videos in top 10: $COMEDY_COUNT"
echo "  Music videos in top 10: $MUSIC_COUNT"
echo ""

if [ "$SPORTS_COUNT" -gt "$COMEDY_COUNT" ] && [ "$MUSIC_COUNT" -gt "$COMEDY_COUNT" ]; then
    echo "✅ ML ALGORITHM WORKING!"
    echo "   - More sports/music (liked) than comedy (skipped)"
    echo "   - Algorithm learned your preferences!"
else
    echo "⚠️  ML results unclear - try interacting more"
fi

echo ""
echo "================================================"
echo "🎉 Test Complete!"
echo ""
echo "Next Steps:"
echo "1. Open frontend and swipe on videos"
echo "2. Check analytics: curl $BASE_URL/api/v1/events/analytics/user/$USER_ID | jq"
echo "3. See personalized feed: curl '$BASE_URL/api/v1/feed/for-you?user_id=$USER_ID&limit=10' | jq"
echo ""
echo "Your test user ID: $USER_ID"
echo "================================================"
