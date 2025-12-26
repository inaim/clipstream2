#!/bin/bash

echo "🚀 Starting Clipstream - TikTok-Style Platform"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"

# Start SurrealDB and Redis
echo ""
echo "🐳 Starting SurrealDB and Redis..."
docker-compose up -d surrealdb redis

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check SurrealDB
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} SurrealDB is ready on port 8000"
else
    echo -e "${YELLOW}⚠${NC}  SurrealDB might not be ready yet (continuing anyway)"
fi

# Check Redis (prefer container ping to avoid missing local redis-cli)
echo "🔍 Checking Redis..."
check_redis() {
    # 1) Use local redis-cli if present
    if command -v redis-cli > /dev/null 2>&1; then
        if redis-cli ping > /dev/null 2>&1; then
            return 0
        fi
    fi
    # 2) Try container exec
    if command -v docker-compose > /dev/null 2>&1; then
        if docker-compose ps redis >/dev/null 2>&1; then
            if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
                return 0
            fi
        fi
    fi
    return 1
}

if check_redis; then
    echo -e "${GREEN}✓${NC} Redis is ready on port 6379"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
    echo "Trying to start Redis manually..."
    docker-compose up -d redis
    sleep 2
    if check_redis; then
        echo -e "${GREEN}✓${NC} Redis started and responding"
    else
        echo -e "${RED}❌ Redis still not responding; install redis-cli or check Docker${NC}"
    fi
fi

# Check if yt-dlp is installed
echo ""
echo "🔍 Checking dependencies..."

if command -v yt-dlp &> /dev/null; then
    echo -e "${GREEN}✓${NC} yt-dlp is installed"
else
    echo -e "${YELLOW}⚠${NC}  yt-dlp not found. Installing..."
    pip install yt-dlp
fi

# Set environment variables
echo ""
echo "⚙️  Setting environment variables..."

export INGEST_DEMO_VIDEOS=false
export ENVIRONMENT=development
export REDIS_URL=redis://localhost:6379/0
export ENABLE_AI_PROCESSING=true
export ENABLE_TOKEN_REWARDS=true

echo -e "${GREEN}✓${NC} Environment configured"

# Start backend
echo ""
echo "🎬 Starting backend with real-time ML..."
echo ""
echo "Backend will start with:"
echo "  - Real playable videos (13 videos)"
echo "  - Infinite scroll feed"
echo "  - Real-time ML feedback (SSE)"
echo "  - Event buffering"
echo ""
echo "Press Ctrl+C to stop the backend"
echo ""
echo "=============================================="
echo ""

cd backend && python3 main.py
