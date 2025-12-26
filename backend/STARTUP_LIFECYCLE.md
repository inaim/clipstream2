# Clipstream Backend Startup Lifecycle

## Overview

The Clipstream backend follows a **4-step startup lifecycle** that ensures the platform is fully initialized and ready to serve users with video content from the moment it launches.

This matches the architecture of production short-form video platforms like TikTok, Reels, and YouTube Shorts.

---

## Startup Lifecycle Phases

### Phase 1: Connect to SurrealDB

**What happens:**
- Establishes connection to SurrealDB (local or cloud)
- Creates both blocking and async database clients
- Authenticates with appropriate credentials (root for dev, namespace user for prod)
- Selects the target namespace and database

**Files involved:**
- `main.py` (lines 54-93)
- `db/surrealdb_client.py`
- `app/startup.py`

**Environment variables:**
```bash
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USER=root
SURREALDB_PASS=root
SURREALDB_NS=clipstream
SURREALDB_DB=production
```

---

### Phase 2: Build Database Schema (Idempotent)

**What happens:**
- Defines all required tables, indexes, and relations
- Creates schema for: `video`, `user`, `event`, `model`, `likes`, `follows`, `comment`, `earnings`, `report`
- Adds optimized indexes for common queries
- Verifies all tables exist and reports counts

**Files involved:**
- `app/startup.py` (function: `build_schema()`, `verify_schema()`)

**Schema tables created:**
- `video` - Video content and metadata
- `user` - User profiles and authentication
- `event` - User interaction tracking for ML
- `model` - ML model metadata and versioning
- `likes` - User-video like relationships (graph)
- `follows` - User-user follow relationships (graph)
- `comment` - Video comments
- `earnings` - Creator token rewards
- `report` - Content moderation reports

**Key features:**
- **Idempotent**: Can be run multiple times safely (won't duplicate or break existing data)
- **Schemaless tables**: Flexible document structure with indexes for performance
- **Graph relations**: Native support for social features (likes, follows)

---

### Phase 3: Start Ingestion Engine

**What happens:**
- Generates or loads initial video content
- Extracts metadata, embeddings, and categories
- Saves videos to database
- Makes them immediately available for the feed

**Files involved:**
- `app/ingestion_engine.py`
- `app/initial_videos.py` (example video sources)

**Ingestion modes:**

1. **Demo Videos** (default for development):
   ```bash
   INGEST_DEMO_VIDEOS=true
   DEMO_VIDEO_COUNT=10
   ```
   - Generates random demo videos for testing
   - Randomized categories, durations, embeddings
   - Perfect for local development

2. **Production Videos**:
   - Load from `app/initial_videos.py`
   - Can pull from CDN, TikTok, YouTube Shorts, S3/GCS, etc.
   - Customize `get_initial_videos()` for your sources

**Ingestion sources supported:**
- Direct CDN URLs
- TikTok video URLs (scraping)
- YouTube Shorts URLs
- Local file uploads
- Cloud storage buckets (S3, GCS)

**Control:**
```bash
# Disable ingestion at startup
INGEST_DEMO_VIDEOS=false

# Change demo video count
DEMO_VIDEO_COUNT=50
```

---

### Phase 4: Platform Ready

**What happens:**
- All systems operational
- Feed endpoint ready to serve videos
- Event logging ready to track user interactions
- Upload endpoint ready to accept new videos
- Users can swipe and generate training data

**Endpoints available:**
- `GET /api/v1/feed/for-you` - Personalized video feed
- `POST /api/v1/events` - Log user interactions
- `POST /api/upload` - Upload new videos
- `GET /health` - System health check
- `GET /` - API status

---

## File Structure

```
backend/
├── main.py                      # FastAPI app with startup lifecycle
├── app/
│   ├── startup.py               # SurrealDB schema builder
│   ├── ingestion_engine.py      # Video ingestion logic
│   ├── scoring.py               # TikTok-style recommendation algorithm
│   ├── event_logger.py          # Event tracking and stats updates
│   └── initial_videos.py        # Example video sources
├── db/
│   └── surrealdb_client.py      # Database connection wrapper
├── api/
│   ├── feed.py                  # Feed endpoints
│   ├── upload.py                # Video upload
│   ├── videos.py                # Video queries
│   └── ...                      # Other API endpoints
├── .env.example                 # Configuration template
└── STARTUP_LIFECYCLE.md         # This file
```

---

## Environment Configuration

### Development (Local)

```bash
# .env
ENVIRONMENT=development
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USER=root
SURREALDB_PASS=root
SURREALDB_NS=clipstream
SURREALDB_DB=production
INGEST_DEMO_VIDEOS=true
DEMO_VIDEO_COUNT=10
```

### Production (Cloud)

```bash
# .env
ENVIRONMENT=production
SURREALDB_URL=wss://your-instance.surrealdb.cloud/rpc
SURREALDB_USER=your_namespace_user
SURREALDB_PASS=your_password
SURREALDB_NS=clipstream
SURREALDB_DB=production
INGEST_DEMO_VIDEOS=false  # Use real video sources
```

---

## Video Scoring Algorithm

The platform uses a **TikTok-style monolithic recommendation algorithm** with three components:

### 1. User Interest (60% weight)
- Category preferences (watch time, like rate)
- Embedding similarity (cosine similarity between user and video)

### 2. Video Quality (30% weight)
- Engagement metrics (watch ratio, completion rate, likes, rewatches)
- Laplace smoothing for low-impression videos
- Age decay (newer videos get boosted)

### 3. Exploration Bonus (10% weight)
- Upper Confidence Bound (UCB) approach
- Encourages showing unseen videos
- Balances exploitation vs exploration

**Implementation:** `app/scoring.py`

**Key functions:**
- `final_score(user, video, now)` - Compute ranking score
- `rank_videos_for_user(user, candidates, limit)` - Sort and rank
- `diversity_rerank(ranked_videos)` - Avoid category clustering

---

## Event Logging & Stats Updates

Every user interaction updates real-time statistics:

### Video Stats Updated:
- `impressions` - Total views
- `total_watch_ratio` - Cumulative watch percentage
- `completions` - Videos watched to end (>80%)
- `early_skips` - Videos skipped early (<20%)
- `likes` - Total likes
- `rewatches` - Repeat views
- `shares` - Share count
- `comments` - Comment count
- `last_seen_ts` - Last impression timestamp

### User Stats Updated:
- `category_stats[category].impressions` - Views per category
- `category_stats[category].watch_ratio` - Watch time per category
- `category_stats[category].likes` - Likes per category
- `video_history[video_id]` - Per-video impression counts
- `total_events` - Total interaction count

**Implementation:** `app/event_logger.py`

**Usage:**
```python
from app.event_logger import log_event

await log_event(db, {
    "user_id": "user:123",
    "video_id": "video:456",
    "event_type": "play_end",
    "timestamp": time.time(),
    "watch_ratio": 0.85,
    "category": "sports",
})
```

---

## Running the Backend

### Local Development

1. **Start SurrealDB:**
   ```bash
   docker-compose up surrealdb redis
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

4. **Run backend:**
   ```bash
   python main.py
   ```

   Or with uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

5. **Check startup logs:**
   ```
   ============================================================
   CLIPSTREAM APP STARTUP LIFECYCLE
   ============================================================
   [STEP 1] Connecting to SurrealDB...
   Blocking SurrealDB client connected
   Async SurrealDB client connected and attached to db_client

   [STEP 2] Building database schema...
   Schema built successfully
   Verified 9 tables

   [STEP 3] Starting video ingestion engine...
   Generating 10 demo videos...
   Ingestion complete: 10/10 videos ingested

   [STEP 4] Platform ready for beta
   ============================================================
   Feed endpoint ready: /api/v1/feed/for-you
   Event logging ready: /api/v1/events
   Video upload ready: /api/upload
   Users can swipe and generate training data
   ============================================================
   Clipstream backend ready - videos ingested, schema built, beta open
   ============================================================
   ```

### Production Deployment

1. **Build Docker image:**
   ```bash
   docker build -t clipstream-backend .
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy clipstream-backend \
     --image gcr.io/your-project/clipstream-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Set environment variables:**
   ```bash
   gcloud run services update clipstream-backend \
     --set-env-vars ENVIRONMENT=production \
     --set-env-vars SURREALDB_URL=wss://... \
     --set-env-vars INGEST_DEMO_VIDEOS=false
   ```

---

## Next Steps

### 1. Cron-based Retraining Job

Create a scheduled job that:
- Aggregates event data
- Retrains user/video embeddings
- Updates model weights
- Improves recommendations over time

**Suggested implementation:**
- Celery Beat task (daily or weekly)
- Cloud Functions (scheduled trigger)
- Kubernetes CronJob

### 2. Live Query Listener for Real-time Updates

Use SurrealDB's Live Queries to:
- Push real-time video updates to clients
- Notify when new videos are ingested
- Stream engagement metrics to dashboards

**Suggested implementation:**
- `LIVE SELECT` queries in SurrealDB
- WebSocket connection to clients
- Server-Sent Events (SSE) for updates

### 3. Category-based Feed Router

Enhance feed generation with:
- Category-specific feeds (`/feed/sports`, `/feed/comedy`)
- Trending by category
- Category exploration mode

**Suggested implementation:**
- Add `category` parameter to feed endpoints
- Filter candidates by category before ranking
- Adjust diversity re-ranking for category feeds

### 4. Analytics Dashboard

Build a monitoring dashboard to:
- View video performance metrics
- Track user engagement trends
- Monitor system health
- Analyze category distribution

**Suggested implementation:**
- Use existing `/api/v1/analytics` endpoints
- Build React dashboard with Chart.js
- Real-time updates via SSE

---

## Troubleshooting

### Schema errors during startup

**Symptom:** "Schema building failed" error
**Solution:**
- Verify SurrealDB is running: `docker ps | grep surrealdb`
- Check credentials in `.env`
- Ensure namespace/database exist
- Check SurrealDB logs: `docker logs <container-id>`

### No videos in feed

**Symptom:** `/api/v1/feed/for-you` returns empty array
**Solution:**
- Check `INGEST_DEMO_VIDEOS=true` in `.env`
- Verify ingestion logs during startup
- Query SurrealDB directly: `SELECT * FROM video;`
- Check database connection

### Slow startup

**Symptom:** Takes >30 seconds to start
**Solution:**
- Reduce `DEMO_VIDEO_COUNT` (default: 10)
- Disable demo ingestion: `INGEST_DEMO_VIDEOS=false`
- Check SurrealDB performance
- Optimize schema verification queries

### Import errors

**Symptom:** `ModuleNotFoundError: No module named 'app'`
**Solution:**
- Ensure running from `backend/` directory
- Check `sys.path` includes backend dir (handled in `main.py`)
- Install dependencies: `pip install -r requirements.txt`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIPSTREAM BACKEND                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Phase 1:    │  │  Phase 2:    │  │  Phase 3:    │     │
│  │  Connect DB  │→ │  Build Schema│→ │  Ingest      │     │
│  │              │  │              │  │  Videos      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Phase 4: Platform Ready                   │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │  Feed    │  │  Events  │  │  Upload  │          │  │
│  │  │  Engine  │  │  Logger  │  │  Handler │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │      TikTok-style Scoring Algorithm         │   │  │
│  │  │  • User Interest (60%)                      │   │  │
│  │  │  • Video Quality (30%)                      │   │  │
│  │  │  • Exploration (10%)                        │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
              ↓                    ↓                    ↓
      ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
      │  SurrealDB   │     │    Redis     │     │   Celery     │
      │              │     │   (Pub/Sub)  │     │   Workers    │
      └──────────────┘     └──────────────┘     └──────────────┘
```

---

## License

Copyright (c) 2025 Finailabz. All rights reserved.

---

**Last Updated:** 2025-12-25
