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
# Always use a project-local venv to avoid system pip issues
VENV_PATH=".clipstream_venv"
VENV_DIR="$(pwd)/${VENV_PATH}"
SYS_PYTHON="$(command -v python3 || echo python3)"

# Helper to (re)create venv cleanly
create_venv() {
    rm -rf "${VENV_DIR}"
    "${SYS_PYTHON}" -m venv "${VENV_DIR}" || {
        echo -e "${RED}❌ Failed to create ${VENV_DIR}${NC}"
        exit 1
    }
}

# Create venv if missing
if [ ! -d "${VENV_DIR}" ]; then
    echo -e "${YELLOW}⚠${NC} ${VENV_DIR} not found; creating it..."
    create_venv
fi

# Prefer python3 inside venv if present, otherwise fall back to python
if [ -x "${VENV_DIR}/bin/python3" ]; then
    PYTHON_CMD="${VENV_DIR}/bin/python3"
elif [ -x "${VENV_DIR}/bin/python" ]; then
    PYTHON_CMD="${VENV_DIR}/bin/python"
else
    PYTHON_CMD="${SYS_PYTHON}"
fi
PIP_CMD="${VENV_DIR}/bin/pip"

# Validate pip; if broken (wrong shebang) or python missing, recreate venv
if ! "${PIP_CMD}" --version >/dev/null 2>&1 || ! [ -x "${PYTHON_CMD}" ]; then
    echo -e "${YELLOW}⚠${NC} Detected broken or incomplete venv at ${VENV_DIR}; recreating..."
    create_venv
    if [ -x "${VENV_DIR}/bin/python3" ]; then
        PYTHON_CMD="${VENV_DIR}/bin/python3"
    else
        PYTHON_CMD="${VENV_DIR}/bin/python"
    fi
    PIP_CMD="${VENV_DIR}/bin/pip"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
echo "Using Python: ${PYTHON_CMD} (absolute: $(realpath "${PYTHON_CMD}" 2>/dev/null || echo 'n/a'))" 

# Install requirements inside the venv
${PIP_CMD} install --upgrade pip
${PIP_CMD} install -r backend/requirements.txt || {
    echo -e "${RED}❌ Failed to install backend requirements${NC}"
    exit 1
}

# Ensure python command exists in venv; recreate if not
if ! [ -x "${PYTHON_CMD}" ]; then
    echo -e "${YELLOW}⚠${NC} Python interpreter missing at ${PYTHON_CMD}; recreating venv..."
    create_venv
    if [ -x "${VENV_PATH}/bin/python3" ]; then
        PYTHON_CMD="${VENV_PATH}/bin/python3"
    else
        PYTHON_CMD="${VENV_PATH}/bin/python"
    fi
    PIP_CMD="${VENV_PATH}/bin/pip"
    ${PIP_CMD} install --upgrade pip
    ${PIP_CMD} install -r backend/requirements.txt || {
        echo -e "${RED}❌ Failed to install backend requirements${NC}"
        exit 1
    }
fi

cd backend && "${PYTHON_CMD}" main.py
