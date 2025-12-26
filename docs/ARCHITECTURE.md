# ClipStream Architecture Documentation

## 📐 System Architecture Overview

ClipStream is built as a modern, scalable hybrid platform combining Web2 performance with Web3 decentralization.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Web App     │  │  Mobile App  │  │  Admin Panel │          │
│  │  (React)     │  │  (React      │  │  (React)     │          │
│  │              │  │   Native)    │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Nginx Reverse Proxy                                    │    │
│  │  • SSL/TLS Termination                                  │    │
│  │  • Rate Limiting (60 req/min, 1000 req/hour)           │    │
│  │  • Load Balancing                                       │    │
│  │  • Static Asset Serving                                 │    │
│  │  • WebSocket Support                                    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  FastAPI Backend (Python 3.11)                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  REST API Endpoints                               │  │    │
│  │  │  • /api/v1/auth/*    - Authentication            │  │    │
│  │  │  • /api/v1/video/*   - Video operations          │  │    │
│  │  │  • /api/v1/users/*   - User management           │  │    │
│  │  │  • /api/v1/feed/*    - Content feeds             │  │    │
│  │  │  • /api/v1/gifts/*   - Monetization              │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  Business Logic Services                          │  │    │
│  │  │  • VideoService      - Video processing          │  │    │
│  │  │  • AIService         - ML/AI operations          │  │    │
│  │  │  • IPFSService       - Decentralized storage     │  │    │
│  │  │  • BlockchainService - Web3 integration          │  │    │
│  │  │  • FeedService       - Recommendation engine     │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  SurrealDB   │  │    Redis     │  │     IPFS     │
│              │  │              │  │              │
│  • Users     │  │  • Sessions  │  │  • Videos    │
│  • Videos    │  │  • Feed      │  │  • Thumbs    │
│  • Comments  │  │  • Cache     │  │  • Assets    │
│  • Likes     │  │  • Queue     │  │              │
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Celery Workers  │
                │                 │
                │ • Video Encode  │
                │ • AI Processing │
                │ • IPFS Upload   │
                │ • Moderation    │
                └─────────────────┘
```

---

## 🗄️ Data Layer

### SurrealDB Schema

```sql
-- Users Table
DEFINE TABLE users SCHEMAFULL;
DEFINE FIELD id ON users TYPE string;
DEFINE FIELD email ON users TYPE string;
DEFINE FIELD username ON users TYPE string;
DEFINE FIELD display_name ON users TYPE string;
DEFINE FIELD avatar_url ON users TYPE option<string>;
DEFINE FIELD bio ON users TYPE option<string>;
DEFINE FIELD created_at ON users TYPE datetime;
DEFINE FIELD updated_at ON users TYPE datetime;
DEFINE FIELD follower_count ON users TYPE int DEFAULT 0;
DEFINE FIELD following_count ON users TYPE int DEFAULT 0;
DEFINE FIELD video_count ON users TYPE int DEFAULT 0;
DEFINE FIELD total_likes ON users TYPE int DEFAULT 0;
DEFINE FIELD wallet_address ON users TYPE option<string>;
DEFINE FIELD watch_balance ON users TYPE float DEFAULT 0.0;

-- Videos Table
DEFINE TABLE videos SCHEMAFULL;
DEFINE FIELD id ON videos TYPE string;
DEFINE FIELD user_id ON videos TYPE string;
DEFINE FIELD title ON videos TYPE string;
DEFINE FIELD description ON videos TYPE option<string>;
DEFINE FIELD ipfs_cid ON videos TYPE string;
DEFINE FIELD cdn_url ON videos TYPE option<string>;
DEFINE FIELD thumbnail_url ON videos TYPE string;
DEFINE FIELD duration ON videos TYPE int;
DEFINE FIELD width ON videos TYPE int;
DEFINE FIELD height ON videos TYPE int;
DEFINE FIELD size_bytes ON videos TYPE int;
DEFINE FIELD view_count ON videos TYPE int DEFAULT 0;
DEFINE FIELD like_count ON videos TYPE int DEFAULT 0;
DEFINE FIELD comment_count ON videos TYPE int DEFAULT 0;
DEFINE FIELD share_count ON videos TYPE int DEFAULT 0;
DEFINE FIELD virality_score ON videos TYPE float DEFAULT 0.0;
DEFINE FIELD clip_embedding ON videos TYPE array<float>;
DEFINE FIELD hashtags ON videos TYPE array<string>;
DEFINE FIELD created_at ON videos TYPE datetime;
DEFINE FIELD updated_at ON videos TYPE datetime;

-- Comments Table
DEFINE TABLE comments SCHEMAFULL;
DEFINE FIELD id ON comments TYPE string;
DEFINE FIELD video_id ON comments TYPE string;
DEFINE FIELD user_id ON comments TYPE string;
DEFINE FIELD text ON comments TYPE string;
DEFINE FIELD parent_id ON comments TYPE option<string>;
DEFINE FIELD like_count ON comments TYPE int DEFAULT 0;
DEFINE FIELD created_at ON comments TYPE datetime;

-- Likes Table (Graph)
DEFINE TABLE likes SCHEMAFULL;
DEFINE FIELD in ON likes TYPE record(videos);
DEFINE FIELD out ON likes TYPE record(users);
DEFINE FIELD created_at ON likes TYPE datetime;

-- Follows Table (Graph)
DEFINE TABLE follows SCHEMAFULL;
DEFINE FIELD in ON follows TYPE record(users);
DEFINE FIELD out ON follows TYPE record(users);
DEFINE FIELD created_at ON follows TYPE datetime;

-- Gifts Table
DEFINE TABLE gifts SCHEMAFULL;
DEFINE FIELD id ON gifts TYPE string;
DEFINE FIELD from_user_id ON gifts TYPE string;
DEFINE FIELD to_user_id ON gifts TYPE string;
DEFINE FIELD video_id ON gifts TYPE string;
DEFINE FIELD gift_type ON gifts TYPE string;
DEFINE FIELD coin_value ON gifts TYPE int;
DEFINE FIELD usd_value ON gifts TYPE float;
DEFINE FIELD created_at ON gifts TYPE datetime;
```

### Redis Cache Structure

```
# User Sessions
session:{user_id} -> {session_data}
TTL: 24 hours

# Feed Cache
feed:for_you:{user_id}:{page} -> [video_ids]
TTL: 5 minutes

feed:following:{user_id}:{page} -> [video_ids]
TTL: 5 minutes

# Video Metadata Cache
video:{video_id} -> {video_data}
TTL: 1 hour

# User Profile Cache
user:{user_id} -> {user_data}
TTL: 30 minutes

# Trending Videos
trending:global -> [video_ids]
TTL: 10 minutes

# Rate Limiting
rate_limit:{user_id}:{endpoint} -> count
TTL: 1 minute
```

---

## 🎬 Video Processing Pipeline

### Upload Flow

```
1. Client Upload
   ├─> Chunked upload via tus.io protocol
   ├─> Progress tracking in Redis
   └─> Temporary storage in /uploads

2. Initial Processing
   ├─> Video validation (format, size, duration)
   ├─> Metadata extraction (FFprobe)
   ├─> Thumbnail generation (3 frames)
   └─> Create database record

3. Async Processing (Celery)
   ├─> Multi-quality encoding
   │   ├─> 360p (640x360, 800kbps)
   │   ├─> 480p (854x480, 1200kbps)
   │   ├─> 720p (1280x720, 2500kbps)
   │   └─> 1080p (1920x1080, 5000kbps)
   │
   ├─> AI Pipeline
   │   ├─> Whisper: Audio transcription
   │   ├─> CLIP: Video embedding (512-dim)
   │   └─> Moderation: NSFW/Violence detection
   │
   └─> Storage Distribution
       ├─> CDN: Hot content (30 days)
       ├─> IPFS: Warm content (30-90 days)
       └─> Filecoin: Cold archive (90+ days)

4. Finalization
   ├─> Update video record with URLs
   ├─> Invalidate cache
   ├─> Notify user
   └─> Index for search
```

### Encoding Settings

```python
# FFmpeg encoding parameters
ENCODING_PRESETS = {
    "360p": {
        "resolution": "640x360",
        "video_bitrate": "800k",
        "audio_bitrate": "96k",
        "preset": "fast",
        "crf": 23,
    },
    "480p": {
        "resolution": "854x480",
        "video_bitrate": "1200k",
        "audio_bitrate": "128k",
        "preset": "fast",
        "crf": 23,
    },
    "720p": {
        "resolution": "1280x720",
        "video_bitrate": "2500k",
        "audio_bitrate": "128k",
        "preset": "medium",
        "crf": 22,
    },
    "1080p": {
        "resolution": "1920x1080",
        "video_bitrate": "5000k",
        "audio_bitrate": "192k",
        "preset": "medium",
        "crf": 21,
    },
}
```

---

## 🤖 AI/ML Pipeline

### CLIP Video Embeddings

```python
# Generate semantic embeddings for video content
import clip
import torch

model, preprocess = clip.load("ViT-B/32")

def generate_video_embedding(video_path: str) -> list[float]:
    """
    Extract frames and generate CLIP embeddings.
    Returns 512-dimensional vector.
    """
    frames = extract_key_frames(video_path, num_frames=8)
    embeddings = []
    
    for frame in frames:
        image = preprocess(frame).unsqueeze(0)
        with torch.no_grad():
            embedding = model.encode_image(image)
        embeddings.append(embedding)
    
    # Average pooling
    avg_embedding = torch.mean(torch.stack(embeddings), dim=0)
    return avg_embedding.cpu().numpy().tolist()
```

### Recommendation Algorithm

```python
def generate_for_you_feed(user_id: str, page: int = 1) -> list[Video]:
    """
    Personalized feed generation using collaborative filtering
    and content-based recommendations.
    """
    # 1. Get user's interaction history
    user_likes = get_user_likes(user_id)
    user_views = get_user_views(user_id)
    
    # 2. Calculate user embedding (average of liked videos)
    user_embedding = calculate_user_embedding(user_likes)
    
    # 3. Find similar videos using cosine similarity
    candidate_videos = find_similar_videos(
        user_embedding,
        limit=1000,
        exclude_seen=True
    )
    
    # 4. Apply engagement-based ranking
    ranked_videos = rank_by_engagement(
        candidate_videos,
        weights={
            "virality_score": 0.4,
            "recency": 0.3,
            "similarity": 0.3,
        }
    )
    
    # 5. Diversity injection (10% random trending)
    final_feed = inject_diversity(ranked_videos, ratio=0.1)
    
    return paginate(final_feed, page=page, per_page=20)
```

### Virality Score Calculation

```python
def calculate_virality_score(video: Video) -> float:
    """
    Calculate virality score based on engagement velocity.
    Updated every 5 minutes by Celery Beat.
    """
    age_hours = (datetime.now() - video.created_at).total_seconds() / 3600
    
    # Engagement metrics
    views_per_hour = video.view_count / max(age_hours, 1)
    likes_per_hour = video.like_count / max(age_hours, 1)
    shares_per_hour = video.share_count / max(age_hours, 1)
    comments_per_hour = video.comment_count / max(age_hours, 1)
    
    # Weighted score
    score = (
        views_per_hour * 1.0 +
        likes_per_hour * 5.0 +
        shares_per_hour * 10.0 +
        comments_per_hour * 8.0
    )
    
    # Time decay (exponential)
    decay_factor = math.exp(-age_hours / 24)
    
    return score * decay_factor
```

---

## 🔗 Blockchain Integration

### $WATCH Token Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract WatchToken is ERC20, Ownable {
    // Merkle root for quarterly distributions
    bytes32 public merkleRoot;
    
    // Track claimed rewards
    mapping(address => mapping(uint256 => bool)) public claimed;
    
    constructor() ERC20("ClipStream Watch", "WATCH") {
        _mint(msg.sender, 1000000000 * 10**18); // 1B tokens
    }
    
    function setMerkleRoot(bytes32 _merkleRoot, uint256 quarter) external onlyOwner {
        merkleRoot = _merkleRoot;
    }
    
    function claimReward(
        uint256 quarter,
        uint256 amount,
        bytes32[] calldata proof
    ) external {
        require(!claimed[msg.sender][quarter], "Already claimed");
        require(verifyProof(proof, msg.sender, amount), "Invalid proof");
        
        claimed[msg.sender][quarter] = true;
        _transfer(owner(), msg.sender, amount);
    }
}
```

### Merkle Distribution System

```python
from merkletree import MerkleTree
import hashlib

def generate_merkle_distribution(creator_earnings: dict[str, float]) -> dict:
    """
    Generate Merkle tree for gas-efficient token distribution.

    Args:
        creator_earnings: {wallet_address: token_amount}

    Returns:
        {
            "merkle_root": "0x...",
            "proofs": {address: [proof_hashes]}
        }
    """
    # Create leaf nodes
    leaves = []
    for address, amount in creator_earnings.items():
        leaf = hashlib.sha256(
            f"{address}{amount}".encode()
        ).hexdigest()
        leaves.append(leaf)

    # Build Merkle tree
    tree = MerkleTree(leaves)
    merkle_root = tree.get_root()

    # Generate proofs for each creator
    proofs = {}
    for i, address in enumerate(creator_earnings.keys()):
        proofs[address] = tree.get_proof(i)

    return {
        "merkle_root": merkle_root,
        "proofs": proofs,
        "total_amount": sum(creator_earnings.values()),
    }
```

---

## 🔄 Async Task Processing

### Celery Configuration

```python
# celeryconfig.py
from celery import Celery
from celery.schedules import crontab

app = Celery('clipstream')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,

    # Worker settings
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Task routing
    task_routes={
        'workers.video_worker.encode_video': {'queue': 'video'},
        'workers.ai_worker.generate_embeddings': {'queue': 'ai'},
        'workers.ipfs_worker.upload_to_ipfs': {'queue': 'ipfs'},
    },

    # Beat schedule
    beat_schedule={
        'update-virality-scores': {
            'task': 'workers.analytics_worker.update_virality_scores',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        'settle-token-rewards': {
            'task': 'workers.blockchain_worker.settle_quarterly_rewards',
            'schedule': crontab(day_of_month='1', hour='0', minute='0'),  # Monthly
        },
        'archive-to-filecoin': {
            'task': 'workers.ipfs_worker.archive_old_videos',
            'schedule': crontab(hour='2', minute='0'),  # Daily at 2 AM
        },
    },
)
```

### Task Examples

```python
# workers/video_worker.py
from celery import Task
import ffmpeg

@app.task(bind=True, max_retries=3)
def encode_video(self, video_id: str, quality: str):
    """
    Encode video to specified quality.
    Retries up to 3 times on failure.
    """
    try:
        video = get_video_by_id(video_id)
        input_path = video.temp_path
        output_path = f"/uploads/{video_id}_{quality}.mp4"

        preset = ENCODING_PRESETS[quality]

        # FFmpeg encoding
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            vcodec='libx264',
            acodec='aac',
            s=preset['resolution'],
            video_bitrate=preset['video_bitrate'],
            audio_bitrate=preset['audio_bitrate'],
            preset=preset['preset'],
            crf=preset['crf'],
        )
        ffmpeg.run(stream, overwrite_output=True)

        # Update database
        update_video_quality(video_id, quality, output_path)

        return {"status": "success", "quality": quality}

    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## 🌐 API Design

### RESTful Endpoints

```
Authentication
├─ POST   /api/v1/auth/register          - Create new account
├─ POST   /api/v1/auth/login             - Login with credentials
├─ POST   /api/v1/auth/logout            - Logout current session
├─ POST   /api/v1/auth/refresh           - Refresh access token
└─ GET    /api/v1/auth/me                - Get current user

Videos
├─ POST   /api/v1/video/upload           - Upload new video
├─ GET    /api/v1/video/{id}             - Get video details
├─ PUT    /api/v1/video/{id}             - Update video metadata
├─ DELETE /api/v1/video/{id}             - Delete video
├─ POST   /api/v1/video/{id}/view        - Record video view
├─ POST   /api/v1/video/{id}/like        - Like/unlike video
├─ GET    /api/v1/video/{id}/comments    - Get video comments
└─ POST   /api/v1/video/{id}/comment     - Add comment

Users
├─ GET    /api/v1/users/{id}             - Get user profile
├─ PUT    /api/v1/users/{id}             - Update profile
├─ GET    /api/v1/users/{id}/videos      - Get user's videos
├─ GET    /api/v1/users/{id}/followers   - Get followers list
├─ GET    /api/v1/users/{id}/following   - Get following list
├─ POST   /api/v1/users/{id}/follow      - Follow/unfollow user
└─ GET    /api/v1/users/{id}/balance     - Get token balance

Feed
├─ GET    /api/v1/feed/for-you           - Personalized feed
├─ GET    /api/v1/feed/following         - Following feed
├─ GET    /api/v1/feed/trending          - Trending videos
└─ GET    /api/v1/feed/hashtag/{tag}     - Hashtag feed

Monetization
├─ POST   /api/v1/gifts/send             - Send virtual gift
├─ GET    /api/v1/gifts/received         - Get received gifts
├─ GET    /api/v1/earnings               - Get earnings summary
└─ POST   /api/v1/tokens/claim           - Claim token rewards

Search
├─ GET    /api/v1/search/videos          - Search videos
├─ GET    /api/v1/search/users           - Search users
└─ GET    /api/v1/search/hashtags        - Search hashtags
```

### Response Format

```json
{
  "success": true,
  "data": {
    "id": "video_123",
    "title": "Amazing Video",
    "user": {
      "id": "user_456",
      "username": "creator",
      "display_name": "Creator Name"
    },
    "stats": {
      "views": 10000,
      "likes": 500,
      "comments": 50
    }
  },
  "meta": {
    "timestamp": "2025-01-15T10:30:00Z",
    "version": "1.0"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VIDEO_NOT_FOUND",
    "message": "The requested video does not exist",
    "details": {
      "video_id": "invalid_123"
    }
  },
  "meta": {
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## 🔒 Security Architecture

### Authentication Flow

```
1. User Login
   ├─> Validate credentials
   ├─> Generate JWT access token (30 min expiry)
   ├─> Generate refresh token (7 day expiry)
   ├─> Store session in Redis
   └─> Return tokens to client

2. Authenticated Request
   ├─> Extract JWT from Authorization header
   ├─> Verify signature and expiry
   ├─> Check session in Redis
   ├─> Load user context
   └─> Process request

3. Token Refresh
   ├─> Validate refresh token
   ├─> Generate new access token
   ├─> Rotate refresh token
   └─> Update session
```

### Rate Limiting Strategy

```python
from fastapi import Request, HTTPException
from redis import Redis
import time

redis = Redis(host='localhost', port=6379, db=0)

async def rate_limit(request: Request, limit: int = 60):
    """
    Rate limiting middleware.
    Default: 60 requests per minute per user.
    """
    user_id = request.state.user.id
    key = f"rate_limit:{user_id}:{int(time.time() / 60)}"

    current = redis.incr(key)
    if current == 1:
        redis.expire(key, 60)

    if current > limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )
```

### Content Security

```python
async def validate_video_upload(file: UploadFile):
    """
    Validate uploaded video for security and compliance.
    """
    # 1. File size check
    if file.size > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        raise ValueError("File too large")

    # 2. File type validation
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise ValueError("Invalid file type")

    # 3. Virus scan (ClamAV)
    if not await scan_for_malware(file):
        raise ValueError("File failed security scan")

    # 4. Content moderation
    moderation_result = await moderate_video(file)
    if moderation_result.nsfw_score > NSFW_THRESHOLD:
        raise ValueError("Content violates community guidelines")

    return True
```

---

## 📊 Monitoring & Observability

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics
video_uploads = Counter('video_uploads_total', 'Total video uploads')
video_views = Counter('video_views_total', 'Total video views')
active_users = Gauge('active_users', 'Currently active users')

# System metrics
celery_queue_length = Gauge(
    'celery_queue_length',
    'Celery queue length',
    ['queue']
)
```

### Logging Strategy

```python
import logging
import structlog

# Structured logging configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info(
    "video_uploaded",
    user_id=user.id,
    video_id=video.id,
    size_mb=video.size / 1024 / 1024,
    duration_seconds=video.duration
)
```

---

## 🚀 Deployment Architecture

### Production Stack

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend

  backend:
    build: ./backend
    environment:
      - APP_ENV=production
      - DEBUG=False
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G

  celery-worker:
    build: ./backend
    command: celery -A workers.video_worker worker
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '4'
          memory: 8G

  surrealdb:
    image: surrealdb/surrealdb:latest
    volumes:
      - surrealdb_data:/data
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 4gb

  ipfs:
    image: ipfs/kubo:latest
    volumes:
      - ipfs_data:/data/ipfs
```

### Scaling Strategy

```
Horizontal Scaling:
├─ Backend API: 3-10 instances (auto-scale based on CPU)
├─ Celery Workers: 4-20 instances (auto-scale based on queue length)
├─ Redis: Master-Replica setup (1 master, 2 replicas)
└─ SurrealDB: Cluster mode (3+ nodes)

Vertical Scaling:
├─ Backend: 2-4 CPU, 4-8GB RAM per instance
├─ Workers: 4-8 CPU, 8-16GB RAM per instance
├─ Database: 4-8 CPU, 8-16GB RAM
└─ Redis: 2-4 CPU, 4-8GB RAM
```

---

## 📈 Performance Optimization

### Caching Layers

```
L1: Browser Cache (Static Assets)
    └─> 1 year cache for immutable assets

L2: CDN Cache (Video Files)
    └─> 30 days cache for video content

L3: Redis Cache (API Responses)
    └─> 5-60 minutes cache for dynamic data

L4: Database Query Cache
    └─> SurrealDB internal caching
```

### Database Optimization

```sql
-- Indexes for fast queries
DEFINE INDEX idx_videos_user ON videos FIELDS user_id;
DEFINE INDEX idx_videos_created ON videos FIELDS created_at;
DEFINE INDEX idx_videos_virality ON videos FIELDS virality_score;
DEFINE INDEX idx_comments_video ON comments FIELDS video_id;
DEFINE INDEX idx_likes_user ON likes FIELDS out;

-- Vector index for similarity search
DEFINE INDEX idx_videos_embedding ON videos FIELDS clip_embedding MTREE DIMENSION 512;
```

---

## 🔧 Development Tools

### Local Development

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend python manage.py migrate

# Access database shell
docker-compose exec surrealdb surreal sql

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Debugging

```python
# Enable debug mode
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()

# Use breakpoints
breakpoint()  # Python 3.7+
```

---

This architecture is designed for:
- ✅ **Scalability**: Handle millions of users
- ✅ **Performance**: Sub-100ms response times
- ✅ **Reliability**: 99.9% uptime
- ✅ **Security**: Enterprise-grade protection
- ✅ **Cost Efficiency**: 70% lower than traditional platforms

