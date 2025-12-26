#!/bin/bash

echo "🧪 TikTok Anti-Detection Test Script"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo "Checking if backend is running..."
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not running!${NC}"
    echo ""
    echo "Start it with:"
    echo "  bash START_TIKTOK_PLATFORM.sh"
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

# Test 1: Stop current ingestion
echo "Step 1: Stopping any running ingestion..."
curl -s -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq -r '.message // "Stopped"'
sleep 2
echo ""

# Test 2: Start with enhanced anti-detection (no proxy)
echo "Step 2: Starting ingestion with enhanced anti-detection..."
echo -e "${YELLOW}Features enabled:${NC}"
echo "  - User agent rotation (8 different browsers)"
echo "  - Randomized viewports"
echo "  - Randomized scroll behavior"
echo "  - Anti-detection scripts"
echo ""

START_RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "videos_per_fetch": 5,
    "fetch_interval": 180
  }')

echo "$START_RESPONSE" | jq '.'
echo ""

# Check if started successfully
if echo "$START_RESPONSE" | jq -e '.success == true' > /dev/null; then
    echo -e "${GREEN}✅ Ingestion started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start ingestion${NC}"
    exit 1
fi

echo ""
echo "Step 3: Triggering immediate test..."
sleep 2

curl -s -X POST http://localhost:8080/api/v1/tiktok-ingestion/trigger-now | jq -r '.message // "Triggered"'
echo ""

# Wait for ingestion to complete
echo "Step 4: Waiting for ingestion cycle to complete (30 seconds)..."
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""
echo ""

# Check status
echo "Step 5: Checking ingestion results..."
echo ""

STATUS=$(curl -s http://localhost:8080/api/v1/tiktok-ingestion/status)
echo "$STATUS" | jq '.'

# Parse results
IS_RUNNING=$(echo "$STATUS" | jq -r '.status.is_running')
SUCCESS_RATE=$(echo "$STATUS" | jq -r '.status.success_rate')
TOTAL_FETCHED=$(echo "$STATUS" | jq -r '.status.total_fetched')
TOTAL_INGESTED=$(echo "$STATUS" | jq -r '.status.total_ingested')
TOTAL_FAILED=$(echo "$STATUS" | jq -r '.status.total_failed')

echo ""
echo "📊 Results:"
echo "==========="
echo "Total Fetched:  $TOTAL_FETCHED"
echo "Total Ingested: $TOTAL_INGESTED"
echo "Total Failed:   $TOTAL_FAILED"
echo "Success Rate:   $(echo "$SUCCESS_RATE * 100" | bc)%"
echo ""

# Evaluate results
if (( $(echo "$SUCCESS_RATE >= 0.5" | bc -l) )); then
    echo -e "${GREEN}🎉 SUCCESS! Anti-detection is working!${NC}"
    echo ""
    echo "Your success rate is good. The enhanced anti-detection features are bypassing TikTok's blocks."
    echo ""
    echo "Next steps:"
    echo "  - Let it run for a few cycles to see consistent results"
    echo "  - Check feed: curl 'http://localhost:8080/api/v1/feed/for-you?user_id=user:test&limit=10' | jq"

elif (( $(echo "$SUCCESS_RATE > 0" | bc -l) )); then
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS${NC}"
    echo ""
    echo "Some videos are downloading, but success rate is low ($SUCCESS_RATE)."
    echo ""
    echo "Try these options:"
    echo "  1. Wait 30-60 minutes (temporary IP block may expire)"
    echo "  2. Add a proxy for better results:"
    echo ""
    echo "     curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"use_browser\": true, \"proxy\": \"http://proxy:port\", \"videos_per_fetch\": 5}'"
    echo ""
    echo "  3. Find free proxies at:"
    echo "     - https://www.proxy-list.download/"
    echo "     - https://free-proxy-list.net/"

else
    echo -e "${RED}❌ STILL BLOCKED${NC}"
    echo ""
    echo "Anti-detection features alone aren't enough. TikTok is still blocking you."
    echo ""
    echo "Recommended solutions:"
    echo ""
    echo "Option 1: Add a Proxy (Best Solution)"
    echo "  1. Get a free proxy from:"
    echo "     - https://www.proxy-list.download/"
    echo "     - https://free-proxy-list.net/"
    echo ""
    echo "  2. Start ingestion with proxy:"
    echo "     curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"use_browser\": true, \"proxy\": \"http://PROXY_IP:PORT\", \"videos_per_fetch\": 5}'"
    echo ""
    echo "Option 2: Wait and Try Again"
    echo "  - TikTok blocks are often temporary (30-60 minutes)"
    echo "  - Stop ingestion: curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop"
    echo "  - Wait 1 hour, then re-run this test"
    echo ""
    echo "Option 3: Use Demo Videos Instead"
    echo "  - Stop TikTok ingestion"
    echo "  - Set ENABLE_TIKTOK_AUTO_INGEST=false"
    echo "  - Set INGEST_DEMO_VIDEOS=true"
    echo "  - Restart with: bash START_TIKTOK_PLATFORM.sh"
fi

echo ""
echo "📝 View detailed logs:"
echo "  tail -f backend/logs/app.log | grep -i tiktok"
echo ""
echo "📖 Read full documentation:"
echo "  cat ANTI_DETECTION_IMPLEMENTATION.md"
echo "  cat FIX_TIKTOK_URLS.md"
echo ""
