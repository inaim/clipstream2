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

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is ready on port 6379"
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
# If the script is run from an activated virtualenv, prefer that interpreter
if [ -n "${VIRTUAL_ENV}" ]; then
    PYTHON_CMD="${VIRTUAL_ENV}/bin/python3"
# Prefer project venv at repo root
elif [ -x ".clipstream_venv/bin/python3" ]; then
    PYTHON_CMD="$(pwd)/.clipstream_venv/bin/python3"
# Then backend-specific venvs
elif [ -x "backend/.clipstream_venv/bin/python3" ]; then
    PYTHON_CMD="$(pwd)/backend/.clipstream_venv/bin/python3"
elif [ -x "backend/venv/bin/python3" ]; then
    PYTHON_CMD="$(pwd)/backend/venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python3)"
else
    PYTHON_CMD="python3"
fi

echo "Using Python: ${PYTHON_CMD}"

# Ensure itsdangerous is available; try installing. If pip refuses due to system-managed Python,
# create a local project venv at .clipstream_venv and install requirements into it.
if ! ${PYTHON_CMD} -c "import importlib; importlib.import_module('itsdangerous')" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} itsdangerous not found for ${PYTHON_CMD} — attempting to install..."
    if ${PYTHON_CMD} -m pip install --upgrade itsdangerous 2> /tmp/its_install_err.txt; then
        echo -e "${GREEN}✓${NC} itsdangerous installed"
    else
        if grep -q "externally-managed-environment" /tmp/its_install_err.txt 2>/dev/null; then
            echo -e "${YELLOW}⚠${NC} pip refused to install into the selected Python (externally-managed)."
            echo "Creating a project virtualenv at .clipstream_venv and installing backend requirements..."
            if [ ! -d ".clipstream_venv" ]; then
                python3 -m venv .clipstream_venv
            fi
            # Activate new venv and install requirements
            source .clipstream_venv/bin/activate
            python3 -m pip install --upgrade pip
            python3 -m pip install -r backend/requirements.txt
            PYTHON_CMD="$(pwd)/.clipstream_venv/bin/python3"
            echo -e "${GREEN}✓${NC} Virtualenv created and dependencies installed"
        else
            echo -e "${RED}❌ Failed to install itsdangerous. See /tmp/its_install_err.txt for details.${NC}"
            cat /tmp/its_install_err.txt || true
            exit 1
        fi
    fi
    rm -f /tmp/its_install_err.txt
fi

# Run the backend
cd backend && ${PYTHON_CMD} main.py
