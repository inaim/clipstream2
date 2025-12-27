# Testing Quick Start Guide

 

Quick reference for testing TikTok video ingestion and AI-based video scoring.

 

## 🎯 Prerequisites

 

```bash

# 1. Install dependencies

cd backend

pip install -r requirements.txt

pip install pytest pytest-asyncio httpx torch numpy scipy

 

# 2. Start services

# Terminal 1: SurrealDB

surreal start --log trace --user root --pass root memory

 

# Terminal 2: Redis

redis-server

 

# Terminal 3: Backend API

cd backend

uvicorn main:app --reload

```

 

## ⚡ Quick Test Commands

 

### Test AI Video Scoring (Unit Tests)

```bash

cd backend/tests

python test_video_scoring.py

```

 

**Tests:**

- ✅ Feature extraction (CLIP, interaction, user features)

- ✅ Model inference (single & multi-objective)

- ✅ Ranking metrics (NDCG, MRR, Precision, Recall)

- ✅ Engagement metrics (CTR, completion rate)

 

**Expected:** All 7 tests pass

 

---

 

### Test TikTok Video Ingestion

```bash

cd backend/tests

python test_tiktok_ingestion.py

```

 

**Tests:**

- ✅ Mock TikTok video generation

- ✅ Batch video ingestion

- ✅ Realistic engagement metrics

 

**Expected:** 5 videos ingested successfully

 

---

 

### Test Full Integration (End-to-End)

```bash

cd backend/tests

python test_integration.py

```

 

**Tests:**

- ✅ Feed API endpoints (for-you, trending)

- ✅ Event recording (views, likes, comments, skips)

- ✅ AI scoring integration

- ✅ Virality detection

 

**Expected:** All 4 integration tests pass

 

---

 

### Generate Sample Training Data

```bash

cd backend/tests

python generate_sample_data.py

```

 

**Generates:**

- 100 users with different behavior profiles

- 500 videos with realistic popularity distribution

- 5,000 interaction events

 

**Output:** `./sample_data/` directory with JSON files

 

---

 

## 🚀 Complete Testing Workflow

 

### Step 1: Verify AI Models Work

```bash

python test_video_scoring.py

```

Expected: `🎉 All tests passed!`

 

### Step 2: Test API Integration

```bash

# Ensure backend is running on localhost:8000

python test_integration.py

```

Expected: `🎉 All integration tests passed!`

 

### Step 3: Simulate TikTok Import

```bash

python test_tiktok_ingestion.py

```

Expected: `✅ Successfully ingested 5 videos`

 

### Step 4: Generate Training Data

```bash

python generate_sample_data.py

```

Expected: Files in `./sample_data/`

 

---

 

## 📊 Expected Test Output

 

### ✅ Successful Test Run

 

```

======================================================================

RUNNING VIDEO SCORING TEST SUITE

======================================================================

 

TEST: Feature Extraction

✅ Feature extraction test PASSED

 

TEST: Model Inference

✅ Model inference test PASSED

   Tower weights: {'content': 0.25, 'interaction': 0.50, 'user': 0.25}

 

TEST: Multi-Objective Model

✅ Multi-objective model test PASSED

 

... (all tests passing)

 

TEST SUMMARY

✅ Passed: 7

❌ Failed: 0

 

Success Rate: 100.0%

 

🎉 All tests passed!

```

 

### ❌ Common Errors

 

**Backend Not Running:**

```

ConnectionError: Cannot connect to http://localhost:8000

```

**Fix:** Start backend with `uvicorn main:app --reload`

 

**Missing Dependencies:**

```

ModuleNotFoundError: No module named 'torch'

```

**Fix:** `pip install torch numpy`

 

**Database Not Running:**

```

SurrealDB connection failed

```

**Fix:** Start SurrealDB: `surreal start --user root --pass root memory`

 

---

 

## 🔬 Testing Individual Components

 

### Test Feature Extraction Only

```python

from ml.features import VideoFeatureExtractor

 

extractor = VideoFeatureExtractor()

 

video = {

    'id': 'video:test',

    'duration': 60,

    'view_count': 1000,

    'like_count': 100,

    'created_at': '2024-01-01T00:00:00Z'

}

 

user = {'id': 'user:test', 'active_hours': [12]}

 

clip, inter, user_feat = extractor.extract_all_features(video, user)

print(f"Features extracted: {clip.shape}, {inter.shape}, {user_feat.shape}")

```

 

### Test Model Scoring Only

```python

from ml.inference import VideoScorerService

 

scorer = VideoScorerService(model_path=None, device='cpu')

 

videos = [...]  # your videos

user_data = {...}  # your user

 

import asyncio

scores = asyncio.run(scorer.score_videos(videos, user_data))

print(f"Top video: {scores[0]}")

```

 

### Test Event Recording Only

```python

from ml.events import VideoEventRecorder

from db.surrealdb_client import db_client

 

async def test_events():

    recorder = VideoEventRecorder(db_client)

 

    await recorder.record_view(

        video_id="video:test",

        user_id="user:test",

        source="for_you"

    )

 

    metrics = await recorder.compute_virality_metrics("video:test")

    print(f"Virality: {metrics}")

 

import asyncio

asyncio.run(test_events())

```

 

---

 

## 📈 Performance Benchmarks

 

Expected performance on standard hardware (CPU):

 

| Operation | Throughput | Latency |

|-----------|------------|---------|

| Feature Extraction | ~50 videos/sec | ~20ms per video |

| Model Inference (batch=32) | ~100 videos/sec | ~10ms per video |

| Event Recording | ~200 events/sec | ~5ms per event |

| Feed Ranking | ~150 videos/sec | ~300ms per feed (50 videos) |

 

---

 

## 🎓 Next Steps After Testing

 

1. **Train Your First Model**

   ```bash

   python -m ml.training.train_scorer --objective engagement --epochs 10

   ```

 

2. **Deploy Trained Model**

   ```python

   from ml.inference import VideoScorerService

   scorer = VideoScorerService(model_path='./models/best_model.pt')

   ```

 

3. **Monitor Production**

   ```python

   from ml.evaluation import ProductionMonitor

   monitor = ProductionMonitor(db_client)

   metrics = await monitor.get_recent_metrics(hours=24)

   ```

 

4. **A/B Test Models**

   ```python

   from ml.inference import MultiModelService

   service = MultiModelService()

   service.add_model('engagement_v1', './models/engagement.pt')

   service.add_model('retention_v2', './models/retention.pt')

   ```

 

---

 

## 📚 Documentation Links

 

- **Detailed Testing Guide:** `backend/tests/README.md`

- **ML System Docs:** `backend/ml/README.md`

- **Architecture:** `ARCHITECTURE.md`

- **API Docs:** `BACKEND_API.md`

 

---

 

## 💡 Tips

 

- **Run tests in order:** Scoring → Integration → Ingestion → Sample Data

- **Check logs:** Tests output detailed info about what they're testing

- **Use sample data:** Generated data is perfect for model training

- **Test configurations:** Try different model objectives (engagement, retention, viral)

- **Monitor performance:** Use `--verbose` flag for detailed output

 

---

 

## 🆘 Getting Help

 

If tests fail:

1. Check prerequisites are running (SurrealDB, Redis, Backend)

2. Review error messages carefully

3. Check `backend/tests/README.md` for detailed troubleshooting

4. Verify Python path: `export PYTHONPATH=../:$PYTHONPATH`

 

Happy testing! 🎉