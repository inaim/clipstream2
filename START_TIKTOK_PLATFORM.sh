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

# Ports (override here if you mapped differently)
SURREAL_PORT=${SURREAL_PORT:-8003}
REDIS_PORT=${REDIS_PORT:-6380}

# Start SurrealDB and Redis
echo ""
echo "🐳 Starting SurrealDB and Redis..."
docker-compose up -d surrealdb redis

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check SurrealDB
if curl -s http://localhost:${SURREAL_PORT}/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} SurrealDB is ready on port ${SURREAL_PORT}"
else
    echo -e "${YELLOW}⚠${NC}  SurrealDB might not be ready yet (continuing anyway)"
fi

# Check Redis
if redis-cli -p ${REDIS_PORT} ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is ready on port ${REDIS_PORT}"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
    echo "Trying to start Redis manually..."
    docker-compose up -d redis
    sleep 2
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

# Set environment variables (match local container port mappings)
echo ""
echo "⚙️  Setting environment variables..."

export INGEST_DEMO_VIDEOS=false
export ENVIRONMENT=development
export REDIS_URL=redis://localhost:${REDIS_PORT}/0
export ENABLE_AI_PROCESSING=true
export ENABLE_TOKEN_REWARDS=true
export SURREALDB_URL=ws://localhost:${SURREAL_PORT}/rpc

echo -e "${GREEN}✓${NC} Environment configured"

# Start backend using the local virtualenv inside backend/
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

# Activate virtualenv (prefer backend/.clipstream_venv, fall back to project .clipstream_venv)
if [ -f "backend/.clipstream_venv/bin/activate" ]; then
    source backend/.clipstream_venv/bin/activate
elif [ -f ".clipstream_venv/bin/activate" ]; then
    source .clipstream_venv/bin/activate
elif [ -f "backend/venv/bin/activate" ]; then
    source backend/venv/bin/activate
else
    echo -e "${YELLOW}⚠${NC} No virtualenv found; using system Python."
fi

# Ensure itsdangerous is available (needed by SessionMiddleware)
python - <<'PYCODE' || pip install itsdangerous
import importlib
import sys
try:
    importlib.import_module("itsdangerous")
except ImportError:
    sys.exit(1)
PYCODE

cd backend && python3 main.py
