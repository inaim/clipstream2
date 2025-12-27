# Testing Guide for Video Ingestion and AI Scoring

This guide explains how to test TikTok video ingestion and the AI-based video scoring system.

## 📁 Test Files Overview

```
tests/
├── README.md                      # This file
├── test_tiktok_ingestion.py      # TikTok video ingestion tests
├── test_video_scoring.py         # AI model and scoring tests
├── test_integration.py           # End-to-end integration tests
└── generate_sample_data.py       # Sample data generator
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt

# Additional test dependencies
pip install pytest pytest-asyncio httpx
```

### 2. Start the Backend

```bash
# Terminal 1: Start SurrealDB
surreal start --log trace --user root --pass root memory

# Terminal 2: Start Redis
redis-server

# Terminal 3: Start FastAPI backend
cd backend
uvicorn main:app --reload
```

### 3. Run Tests

```bash
cd backend/tests

# Run all test suites
python test_video_scoring.py      # Unit tests for AI models
python test_tiktok_ingestion.py   # TikTok ingestion simulation
python test_integration.py        # End-to-end integration tests
```

---

## 🎯 Test Suite 1: TikTok Video Ingestion

### What It Tests

- Mock TikTok video scraping
- Video metadata extraction
- Batch video ingestion into ClipStream
- Video creation via API

### Run the Test

```bash
python test_tiktok_ingestion.py
```

### Expected Output

```
==================================================
Testing TikTok Video Ingestion
==================================================

Generated 5 mock TikTok videos:
  - mock_tiktok_000000: 🔥 This trend is going viral! (523,142 views, 125,554 likes)
  - mock_tiktok_000001: You won't believe this hack! (2,341 views, 351 likes)
  ...

✅ Successfully ingested 5 videos
```

### How It Works

1. **MockTikTokScraper**: Generates realistic TikTok video metadata
2. **TikTokVideoIngester**: Sends videos to ClipStream backend
3. Creates videos with realistic engagement metrics

### Customize the Test

```python
# In test_tiktok_ingestion.py

# Change number of videos
scraper.scrape_trending(count=10)  # default: 5

# Scrape by hashtag
scraper.scrape_by_hashtag('#dance', count=20)

# Change backend URL
ingester = TikTokVideoIngester(
    backend_url="http://production-server:8000"
)
```

---

## 🧠 Test Suite 2: Video Scoring Model

### What It Tests

- Feature extraction from videos and users
- Model inference and scoring
- Multi-objective models
- Model configurations
- Ranking metrics
- Engagement metrics
- Batch processing

### Run the Test

```bash
python test_video_scoring.py
```

### Expected Output

```
======================================================================
RUNNING VIDEO SCORING TEST SUITE
======================================================================

==================================================
TEST: Feature Extraction
==================================================
✅ Feature extraction test PASSED
   CLIP embedding: (512,)
   Interaction features: (8,)
   User features: (6,)

==================================================
TEST: Model Inference
==================================================
✅ Model inference test PASSED
   Batch size: 5
   Output shape: (5, 1)
   Score range: [-0.523, 0.812]
   Tower weights: {'content': 0.25, 'interaction': 0.50, 'user': 0.25}

...

======================================================================
TEST SUMMARY
======================================================================
✅ Passed: 7
❌ Failed: 0

Success Rate: 100.0%

🎉 All tests passed!
```

### Individual Tests

#### Test 1: Feature Extraction
Validates that features are extracted correctly from video and user data:
- CLIP embeddings (512 dimensions)
- Interaction features (8 dimensions)
- User features (6 dimensions)

#### Test 2: Model Inference
Tests the neural network forward pass:
- Batch processing
- Output shape validation
- NaN/Inf detection
- Tower weight normalization

#### Test 3: Multi-Objective Model
Tests different optimization objectives:
- Engagement
- Retention
- Discovery
- Monetization

#### Test 4: Model Configurations
Validates 6 pre-configured objectives:
- Tower weights sum to 1.0
- Feature weights are reasonable
- Hyperparameters are valid

#### Test 5: Ranking Metrics
Tests evaluation metrics:
- NDCG@K (ranking quality)
- MRR (first relevant position)
- Precision@K (relevant in top K)
- Recall@K (coverage)

#### Test 6: Engagement Metrics
Tests engagement calculations:
- Click-through rate (CTR)
- Engagement rate
- Completion rate
- Watch time ratio

#### Test 7: Batch Processing
Tests efficiency of batch feature extraction:
- Processes 50 videos
- Measures throughput (videos/sec)

---

## 🔗 Test Suite 3: Integration Tests

### What It Tests

- End-to-end video ingestion
- Event recording (views, likes, skips)
- AI scoring with feed API
- Virality detection
- Feed personalization

### Run the Test

```bash
python test_integration.py
```

### Expected Output

```
======================================================================
RUNNING INTEGRATION TEST SUITE
======================================================================

==================================================
SETUP: Creating Test Data
==================================================
Creating 5 test videos...
  ✅ Created video: video:abc123
  ✅ Created video: video:def456
  ...

✅ Test data setup complete:
   Videos created: 5
   Test user ID: user:test123

==================================================
TEST: Feed API Endpoints
==================================================

1. Testing For You feed (no AI)...
   ✅ Received 5 videos

2. Testing For You feed (with AI)...
   ✅ Received 5 videos (AI ranking attempted)

3. Testing Trending feed...
   ✅ Received 5 videos

4. Testing debug/recent-videos endpoint...
   ✅ Received 5 videos

📊 Feed API Tests: 4/4 passed

==================================================
TEST: Video Event Recording
==================================================
Recording events for video video:abc123...
  ✅ View event recorded
  ✅ Watch event recorded (45s / 60s)
  ✅ Like event recorded
  ✅ Comment event recorded
  ✅ Skip event recorded
  ✅ Retrieved 5 user events
  ✅ Virality metrics: velocity=12.50 views/hour

✅ Event recording test PASSED

==================================================
TEST: AI Scoring Integration
==================================================
  ✅ Scoring service initialized
  ✅ Scored 10 videos
  ✅ Score range: [-0.234, 0.567]
  ✅ Model info: {'model_type': 'single', 'device': 'cpu', ...}

✅ AI scoring integration test PASSED

==================================================
TEST: Virality Detection
==================================================
Simulating viral activity for video:abc123...
  ✅ Simulated 20 user interactions

Virality Metrics:
  Is Viral: True
  Is Trending: True
  Velocity: 120.50 views/hour
  Engagement Rate: 35.00%
  Total Views (24h): 20
  Total Engagements (24h): 7

✅ Virality detection test PASSED

======================================================================
INTEGRATION TEST SUMMARY
======================================================================
✅ Passed: 4
❌ Failed: 0

Success Rate: 100.0%

🎉 All integration tests passed!
```

### Prerequisites

The integration tests require:
- ✅ Backend API running on `http://localhost:8000`
- ✅ SurrealDB running
- ✅ Redis running

---

## 📊 Sample Data Generator

### What It Generates

- **Users**: Different behavior archetypes (casual, engaged, power user, etc.)
- **Videos**: Realistic popularity distribution (low, medium, high, viral)
- **Interactions**: User-video events (views, likes, comments, skips)

### Run the Generator

```bash
python generate_sample_data.py
```

### Expected Output

```
======================================================================
SAMPLE DATA GENERATOR
======================================================================

Generating 100 sample users...
Generated 100 users with different behavior profiles

Generating 500 sample videos...
Generated 500 videos across popularity tiers:
  low     : 300 videos (60.0%)
  medium  : 125 videos (25.0%)
  high    :  50 videos (10.0%)
  viral   :  25 videos (5.0%)

Generating interactions (50 per user)...
Generated 5000 interaction events

Event type distribution:
  watch          :  2800 (56.0%)
  skip           :  1600 (32.0%)
  complete       :   400 (8.0%)
  like           :   150 (3.0%)
  comment        :    40 (0.8%)
  share          :    10 (0.2%)

======================================================================
GENERATION COMPLETE
======================================================================
Total users: 100
Total videos: 500
Total interactions: 5000

Data saved to: ./sample_data/
```

### Generated Files

```
sample_data/
├── users.json           # User profiles with behavior archetypes
├── videos.json          # Videos with engagement metrics
├── interactions.json    # User-video interaction events
└── summary.json         # Generation statistics
```

### Use the Sample Data

```python
import json

# Load generated data
with open('sample_data/users.json') as f:
    users = json.load(f)

with open('sample_data/videos.json') as f:
    videos = json.load(f)

with open('sample_data/interactions.json') as f:
    interactions = json.load(f)

# Use for training
from ml.training import VideoInteractionDataset, VideoScorerTrainer

dataset = VideoInteractionDataset(
    interactions=interactions,
    feature_extractor=...,
    label_type='engagement'
)

trainer = VideoScorerTrainer(...)
trainer.train(train_dataset=dataset, epochs=10)
```

---

## 📖 Complete Testing Workflow

### Step 1: Generate Sample Data

```bash
cd backend/tests
python generate_sample_data.py
```

This creates realistic test data with:
- 100 users with different behaviors
- 500 videos with varying popularity
- 5,000 interaction events

### Step 2: Test AI Scoring Models

```bash
python test_video_scoring.py
```

Validates:
- ✅ Feature extraction
- ✅ Model inference
- ✅ Multi-objective scoring
- ✅ Ranking metrics

### Step 3: Test Integration

```bash
# Ensure backend is running
python test_integration.py
```

Tests the full pipeline:
- ✅ API endpoints
- ✅ Event recording
- ✅ AI scoring
- ✅ Virality detection

### Step 4: Test TikTok Ingestion

```bash
python test_tiktok_ingestion.py
```

Simulates importing videos:
- ✅ Mock TikTok scraping
- ✅ Batch ingestion
- ✅ Metadata extraction

---

## 🔧 Troubleshooting

### Import Errors

```
ModuleNotFoundError: No module named 'ml'
```

**Fix**: Ensure you're running from the correct directory:
```bash
cd backend/tests
export PYTHONPATH=../:$PYTHONPATH
python test_video_scoring.py
```

### Connection Errors

```
ConnectionError: Cannot connect to backend
```

**Fix**: Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

### Database Errors

```
SurrealDB connection failed
```

**Fix**: Start SurrealDB:
```bash
surreal start --log trace --user root --pass root memory
```

### Redis Errors

```
Redis connection failed
```

**Fix**: Start Redis:
```bash
redis-server
```

---

## 📝 Writing Custom Tests

### Example: Custom Video Scoring Test

```python
from ml.models import VideoScoringModel
from ml.features import VideoFeatureExtractor
import torch

# Initialize
model = VideoScoringModel()
extractor = VideoFeatureExtractor()

# Your video data
video = {
    'id': 'video:test',
    'duration': 60,
    'view_count': 1000,
    'like_count': 100,
    'hashtags': ['test'],
    'created_at': '2024-01-01T00:00:00Z'
}

user = {'id': 'user:test'}

# Extract features
clip_emb, inter_feat, user_feat = extractor.extract_all_features(
    video_data=video,
    user_data=user
)

# Score
clip_emb_t = torch.from_numpy(clip_emb).unsqueeze(0)
inter_feat_t = torch.from_numpy(inter_feat).unsqueeze(0)
user_feat_t = torch.from_numpy(user_feat).unsqueeze(0)

with torch.no_grad():
    score = model(clip_emb_t, inter_feat_t, user_feat_t)

print(f"Video score: {score.item():.3f}")
```

### Example: Custom Event Recording Test

```python
from ml.events import VideoEventRecorder, EventType
from db.surrealdb_client import db_client

async def test_custom_event():
    recorder = VideoEventRecorder(db_client)

    # Record custom interaction
    await recorder.record_watch(
        video_id="video:custom",
        user_id="user:tester",
        watch_time=30.0,
        video_duration=60.0,
        source="test"
    )

    # Check virality
    metrics = await recorder.compute_virality_metrics("video:custom")
    print(f"Virality: {metrics}")

# Run
import asyncio
asyncio.run(test_custom_event())
```

---

## 📚 Additional Resources

- **ML Documentation**: `backend/ml/README.md`
- **API Documentation**: `ARCHITECTURE.md`
- **Model Configs**: `backend/ml/config/model_configs.py`
- **Feature Engineering**: `backend/ml/features/feature_engineering.py`

---

## 🎯 Test Coverage

| Component | Unit Tests | Integration Tests | Status |
|-----------|------------|-------------------|--------|
| Feature Extraction | ✅ | ✅ | Complete |
| Model Inference | ✅ | ✅ | Complete |
| Event Recording | ⚠️ | ✅ | Integration only |
| Feed API | ❌ | ✅ | Integration only |
| Virality Detection | ❌ | ✅ | Integration only |
| TikTok Ingestion | ⚠️ | ⚠️ | Mock only |

✅ = Fully tested
⚠️ = Partially tested
❌ = No tests

---

## 🚀 Next Steps

1. **Train a Real Model**: Use generated sample data to train your first model
2. **Deploy to Production**: Load trained model in production with `VideoScorerService`
3. **Monitor Performance**: Use `ProductionMonitor` to track metrics
4. **A/B Test Models**: Try different configurations to optimize for your goals

Happy testing! 🎉
