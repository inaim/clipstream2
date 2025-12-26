#!/bin/bash

echo "📚 Organizing Documentation for RAG"
echo "===================================="
echo ""

WORKTREE="/Users/issamnaim/.claude-worktrees/clipstream/cranky-johnson"
DOCS_DIR="$WORKTREE/docs"

# Create directory structure
mkdir -p "$DOCS_DIR/help"
mkdir -p "$DOCS_DIR/api"
mkdir -p "$DOCS_DIR/architecture"
mkdir -p "$DOCS_DIR/guides"

echo "📁 Moving documents to organized structure..."
echo ""

# === HELP DOCUMENTS ===
echo "📖 Help & Quick Start..."

# Quick Start (already created)
# Testing Guide
cat > "$DOCS_DIR/help/TESTING.md" << 'EOF'
# 🧪 Testing Guide

Complete testing guide for Clipstream ML algorithm.

See: `../TIKTOK_REALTIME_GUIDE.md` (original) or `TESTING_GUIDE.md` (backend)

## Quick Test

```bash
# Run automated test
bash TEST_NOW.sh
```

## Multi-User Testing

See full guide in backend/TESTING_GUIDE.md

EOF

# Troubleshooting
cat > "$DOCS_DIR/help/TROUBLESHOOTING.md" << 'EOF'
# 🔧 Troubleshooting Guide

## Common Issues

### Redis Not Connected
```bash
docker-compose up -d redis
redis-cli ping  # Should return PONG
```

### SSE Not Working
```bash
# Test SSE manually
curl -N http://localhost:8080/api/v1/realtime/stream/ml-feedback?user_id=user:test1

# Check CORS in backend/.env
ALLOWED_ORIGINS=["http://localhost:8000"]
```

### Videos Not Playing
```bash
# Check video URLs
curl http://localhost:8080/api/v1/feed/for-you?limit=1 | jq '.[0].cdn_url'

# Should see Google CDN URLs
```

### Slow Searches
```bash
# Check if using FAISS
curl http://localhost:8080/api/v1/embeddings/stats | jq '.stats.using_faiss'

# Install if missing
pip install faiss-cpu
```

### Out of Memory
```bash
# Reduce cache size in backend/app/embeddings.py
cache_size=1000  # Instead of 10000
```

See full troubleshooting in original guides.
EOF

echo "  ✓ QUICK_START.md"
echo "  ✓ TESTING.md"
echo "  ✓ TROUBLESHOOTING.md"
echo ""

# === API DOCUMENTS ===
echo "🔌 API Reference..."

cat > "$DOCS_DIR/api/ENDPOINTS.md" << 'EOF'
# 📡 API Endpoints Reference

Complete API reference for Clipstream.

## Infinite Feed

```
POST /api/v1/infinite/infinite         - Get infinite scroll feed
POST /api/v1/infinite/events/batch     - Batch event logging
GET  /api/v1/infinite/prefetch         - Prefetch next batch
POST /api/v1/infinite/refresh          - Refresh feed
GET  /api/v1/infinite/analytics/feed-quality - Feed metrics
```

## Real-time Events

```
GET  /api/v1/realtime/stream/ml-feedback - SSE stream
POST /api/v1/realtime/stream/event     - Log event with feedback
POST /api/v1/realtime/stream/event/buffered - Buffered logging
```

## Embeddings

```
POST /api/v1/embeddings/add            - Add embedding
POST /api/v1/embeddings/batch          - Batch add
POST /api/v1/embeddings/search         - Search similar
GET  /api/v1/embeddings/similar/{id}   - Get similar videos
GET  /api/v1/embeddings/get/{id}       - Get embedding
DELETE /api/v1/embeddings/remove/{id}  - Remove embedding
GET  /api/v1/embeddings/stats          - Get stats
POST /api/v1/embeddings/generate-dummy - Generate test data
```

## Authentication

```
POST /api/v1/auth/register             - Register user
POST /api/v1/auth/login                - Login
GET  /api/v1/auth/me                   - Get current user
```

## Analytics

```
GET /api/v1/events/analytics/user/{id}  - User analytics
GET /api/v1/events/analytics/video/{id} - Video analytics
```

See detailed examples in original guides.
EOF

cat > "$DOCS_DIR/api/INFINITE_FEED.md" << 'EOF'
# ∞ Infinite Scroll Feed API

Cursor-based pagination for infinite scroll.

## Get Feed

```bash
POST /api/v1/infinite/infinite
{
  "user_id": "user:test1",
  "cursor": null,
  "limit": 10,
  "exclude_seen": true
}
```

## Response

```json
{
  "videos": [...],
  "next_cursor": "video:10",
  "has_more": true,
  "total_candidates": 50,
  "personalization_score": 0.735
}
```

See full documentation in TIKTOK_REALTIME_GUIDE.md
EOF

cat > "$DOCS_DIR/api/REALTIME_EVENTS.md" << 'EOF'
# ⚡ Real-time Events API

Server-Sent Events (SSE) for real-time ML feedback.

## Subscribe to ML Feedback

```javascript
const eventSource = new EventSource(
  'http://localhost:8080/api/v1/realtime/stream/ml-feedback?user_id=user:test1'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('ML Update:', data.feedback);
};
```

## Log Event

```bash
POST /api/v1/realtime/stream/event
{
  "user_id": "user:test1",
  "video_id": "video:5",
  "event_type": "like",
  "watch_ratio": 0.85,
  "category": "sports"
}
```

See full documentation in TIKTOK_REALTIME_GUIDE.md
EOF

cat > "$DOCS_DIR/api/EMBEDDINGS.md" << 'EOF'
# 🎯 Embeddings API

Collision-less embedding similarity search.

## Add Embedding

```bash
POST /api/v1/embeddings/add
{
  "video_id": "video:1",
  "category": "sports",
  "embedding": [0.12, ...],  # Optional, auto-generated if omitted
  "metadata": {}
}
```

## Search Similar

```bash
GET /api/v1/embeddings/similar/video:5?k=10&min_similarity=0.7
```

## Get Stats

```bash
GET /api/v1/embeddings/stats
```

See full documentation in EMBEDDINGS_GUIDE.md
EOF

echo "  ✓ ENDPOINTS.md"
echo "  ✓ INFINITE_FEED.md"
echo "  ✓ REALTIME_EVENTS.md"
echo "  ✓ EMBEDDINGS.md"
echo ""

# === GUIDES ===
echo "📘 Guides..."

# Copy/link existing guides
if [ -f "$WORKTREE/EMBEDDINGS_GUIDE.md" ]; then
    cp "$WORKTREE/EMBEDDINGS_GUIDE.md" "$DOCS_DIR/guides/EMBEDDINGS.md"
    echo "  ✓ EMBEDDINGS.md (from EMBEDDINGS_GUIDE.md)"
fi

cat > "$DOCS_DIR/guides/REALTIME_ML.md" << 'EOF'
# 🤖 Real-time ML Guide

Complete guide to real-time ML feedback system.

See full documentation in: `../TIKTOK_REALTIME_GUIDE.md`

## Quick Overview

- SSE for instant feedback
- Redis Pub/Sub for broadcasting
- Event buffering for high volume
- ML updates in ~100ms

## Architecture

```
User Swipes → Event Logged → ML Updates →
SSE Publishes → Frontend Receives → UI Updates
```

Performance: ~100ms end-to-end
EOF

cat > "$DOCS_DIR/guides/TIKTOK_INGESTION.md" << 'EOF'
# 🎬 TikTok Video Ingestion

Download and ingest real TikTok videos.

## Setup

```bash
pip install yt-dlp
```

## Create Ingestion Script

```python
import asyncio
from app.tiktok_scraper import download_and_prepare_tiktok_videos
from app.ingestion_engine import ingest_initial_videos
from db.surrealdb_client import db_client

async def ingest_tiktoks():
    await db_client.connect()
    async_db = getattr(db_client, "async_db")

    urls = [
        "https://www.tiktok.com/@nike/video/...",
        "https://www.tiktok.com/@espn/video/...",
    ]

    videos = await download_and_prepare_tiktok_videos(urls)
    result = await ingest_initial_videos(async_db, videos)

    print(f"Ingested {result['ingested']} videos")

asyncio.run(ingest_tiktoks())
```

## Run

```bash
python3 ingest_tiktok.py
```

See full guide in TIKTOK_REALTIME_GUIDE.md
EOF

echo "  ✓ REALTIME_ML.md"
echo "  ✓ TIKTOK_INGESTION.md"
echo ""

# === ARCHITECTURE ===
echo "🏗️  Architecture..."

cat > "$DOCS_DIR/architecture/OVERVIEW.md" << 'EOF'
# 🏗️ System Architecture

High-level architecture of Clipstream platform.

## Components

```
┌─────────────────────────────────────────────┐
│         Frontend (Swipe UI)                 │
│  - TikTok-style gestures                    │
│  - Infinite scroll                          │
│  - Real-time ML feedback                    │
└──────────────┬──────────────────────────────┘
               │ HTTP/SSE
┌──────────────▼──────────────────────────────┐
│           Backend APIs                       │
│  - Infinite Feed API                        │
│  - Real-time Events API                     │
│  - Embeddings API                           │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Storage & ML Layer                   │
│  - SurrealDB (metadata)                     │
│  - Redis (pub/sub)                          │
│  - FAISS (embeddings)                       │
│  - ML Algorithm (ranking)                   │
└──────────────────────────────────────────────┘
```

See detailed architecture in original docs.
EOF

cat > "$DOCS_DIR/architecture/ML_ALGORITHM.md" << 'EOF'
# 🤖 ML Ranking Algorithm

TikTok-style 3-component scoring algorithm.

## Components

1. **User Interest (60%)**
   - Category preferences
   - Embedding similarity
   - Watch history

2. **Video Quality (30%)**
   - Engagement metrics
   - Age decay
   - Laplace smoothing

3. **Exploration (10%)**
   - UCB discovery bonus
   - Unseen content boost

## Formula

```python
final_score = (
    0.6 * user_interest_score +
    0.3 * video_quality_score +
    0.1 * exploration_bonus
)
```

## Diversity Re-ranking

Prevents category clustering by penalizing consecutive videos from same category.

See full details in backend/app/scoring.py
EOF

cat > "$DOCS_DIR/architecture/DATABASE_SCHEMA.md" << 'EOF'
# 🗄️ Database Schema

SurrealDB schema with 9 tables.

## Tables

1. **video** - Video metadata & stats
2. **user** - User profiles & preferences
3. **event** - User interaction events
4. **model** - ML model versions
5. **likes** - Like relations
6. **follows** - Follow relations
7. **comment** - Comments
8. **earnings** - Creator earnings
9. **report** - Content reports

## Indexes

- `video_category_idx` - Category filtering
- `video_last_seen_idx` - Feed ordering
- `event_timestamp_idx` - Event queries

See full schema in backend/app/startup.py
EOF

cat > "$DOCS_DIR/architecture/SCALING.md" << 'EOF'
# 📈 Scaling Guide

Scale Clipstream to TikTok-level traffic.

## Capacity

- **Videos:** Billions (FAISS sharding)
- **Events:** Millions/second (buffering)
- **Users:** Unlimited (cursor pagination)

## Optimizations

### 1. FAISS GPU

```python
table = CollisionlessEmbeddingTable(use_gpu=True)
```

### 2. Redis Cluster

```yaml
redis:
  cluster:
    nodes: 6
    replicas: 1
```

### 3. CDN for Videos

- Use Cloudflare or CloudFront
- Serve videos from edge locations
- Reduce latency to <50ms

### 4. Event Buffering

- Buffer 100 events per batch
- Auto-flush every 1 second
- Reduces DB writes by 100x

See full guide in original docs.
EOF

echo "  ✓ OVERVIEW.md"
echo "  ✓ ML_ALGORITHM.md"
echo "  ✓ DATABASE_SCHEMA.md"
echo "  ✓ SCALING.md"
echo ""

# === CLEANUP ===
echo "🧹 Cleaning up unused files..."

# Mark old files as deprecated (don't delete, just note)
cat > "$WORKTREE/DEPRECATED_DOCS.txt" << 'EOF'
The following files have been reorganized into docs/ folder:

- TIKTOK_REALTIME_GUIDE.md → docs/guides/REALTIME_ML.md + docs/api/*
- TIKTOK_COMPLETE_SUMMARY.md → docs/architecture/OVERVIEW.md
- EMBEDDINGS_GUIDE.md → docs/guides/EMBEDDINGS.md
- START_HERE_TIKTOK.md → docs/help/QUICK_START.md
- FINAL_COMPLETE.md → docs/README.md

Original files kept for reference.
New structure optimized for RAG chatbot.
EOF

echo "  ✓ Created deprecation notice"
echo ""

echo "✅ Documentation organized!"
echo ""
echo "Structure:"
echo "  docs/"
echo "    ├── README.md (main index)"
echo "    ├── RAG_INDEX.json (chatbot knowledge base)"
echo "    ├── help/"
echo "    │   ├── QUICK_START.md"
echo "    │   ├── TESTING.md"
echo "    │   └── TROUBLESHOOTING.md"
echo "    ├── api/"
echo "    │   ├── ENDPOINTS.md"
echo "    │   ├── INFINITE_FEED.md"
echo "    │   ├── REALTIME_EVENTS.md"
echo "    │   └── EMBEDDINGS.md"
echo "    ├── architecture/"
echo "    │   ├── OVERVIEW.md"
echo "    │   ├── ML_ALGORITHM.md"
echo "    │   ├── DATABASE_SCHEMA.md"
echo "    │   └── SCALING.md"
echo "    └── guides/"
echo "        ├── EMBEDDINGS.md"
echo "        ├── REALTIME_ML.md"
echo "        └── TIKTOK_INGESTION.md"
echo ""
echo "📚 RAG-ready knowledge base: docs/RAG_INDEX.json"
echo ""
