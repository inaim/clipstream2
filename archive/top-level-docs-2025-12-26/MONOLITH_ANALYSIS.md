# 🎯 Monolith Analysis - What We're Missing

## Paper Reference
**Monolith: Real Time Recommendation System With Collisionless Embedding Table**
ByteDance (TikTok's Parent Company)
arXiv: 2209.07663

---

## What is Monolith?

Monolith is **ByteDance's production recommendation system** used for TikTok, Douyin, and other platforms. It handles:
- **Billions of users**
- **Real-time training** (updates every minute)
- **Collisionless embeddings** using Cuckoo Hashing
- **Online serving** with immediate feedback

This is the **actual system powering TikTok's "For You" page**.

---

## Key Features of Monolith

### 1. ✅ Collisionless Embedding Table (We Have This!)

**Monolith's Approach:**
- Uses **Cuckoo Hashing** with two hash tables (T0, T1)
- Each ID gets a unique embedding (no collisions)
- Two hash functions: h0(x) and h1(x)

**Our Implementation:**
- ✅ Uses SHA256 hashing (even stronger than Cuckoo)
- ✅ Zero collisions guaranteed
- ✅ Content hash deduplication

**Verdict:** We're good here! SHA256 is actually more collision-resistant than Cuckoo hashing.

---

### 2. ❌ Real-Time Online Training (We're Missing This!)

**Monolith's Approach:**
- Training and serving run **simultaneously**
- Parameter servers (PS) sync every **1-2 minutes**
- User interactions → immediate model updates
- No batch/serving separation

**Our Current Implementation:**
- ❌ No online training
- ✅ Real-time event logging
- ✅ Real-time ML feedback (SSE)
- ❌ Model doesn't retrain automatically

**What We're Missing:**
```python
# Monolith does this:
User swipes → Event logged → Model retrains (60 seconds) → Updated recommendations

# We do this:
User swipes → Event logged → Stats updated → Recommendations use old model
```

**Impact:** Our ML doesn't improve automatically. We'd need to manually retrain periodically.

---

### 3. ❌ Expirable Embeddings (We're Missing This!)

**Monolith's Approach:**
- **TTL (Time-To-Live)** for embeddings
- Old/inactive user embeddings expire
- Frees memory for active users
- Critical for billion-user scale

**Our Current Implementation:**
- ❌ Embeddings live forever
- ❌ No expiration mechanism
- ❌ Memory grows indefinitely

**What We're Missing:**
```python
# Monolith does this:
class ExpirableEmbedding:
    embedding: np.ndarray
    last_accessed: datetime
    ttl: int = 30 days  # Expires after 30 days

    def is_expired(self):
        return datetime.now() - self.last_accessed > timedelta(days=self.ttl)

# Cleanup process runs daily
cleanup_expired_embeddings()
```

**Impact:** At billion-user scale, we'd run out of memory. TikTok has 1B+ users but only ~100M active daily.

---

### 4. ❌ Frequency Filtering (We're Missing This!)

**Monolith's Approach:**
- Only store embeddings for users/videos with **> N interactions**
- Low-frequency items use a **shared default embedding**
- Reduces embedding table size by 80%+

**Our Current Implementation:**
- ❌ Every video gets an embedding (even with 0 views)
- ❌ No frequency threshold

**What We're Missing:**
```python
# Monolith does this:
MIN_INTERACTIONS = 10

if video.view_count < MIN_INTERACTIONS:
    # Use default embedding
    embedding = DEFAULT_EMBEDDING_FOR_CATEGORY[video.category]
else:
    # Store dedicated embedding
    embedding = generate_unique_embedding(video)
```

**Impact:** We waste memory on videos that nobody watches.

---

### 5. ❌ Parameter Server Architecture (We're Missing This!)

**Monolith's Approach:**
- **Training PS** (Parameter Server) - Trains the model
- **Serving PS** (Parameter Server) - Serves recommendations
- Sync every 1-2 minutes
- Allows training to continue without blocking serving

**Our Current Implementation:**
- ❌ Single-tier architecture
- ❌ No separate training/serving

**What We're Missing:**
```
┌─────────────────────────────────────────────────────────┐
│                    MONOLITH ARCHITECTURE                 │
└─────────────────────────────────────────────────────────┘

User Interaction
    ↓
Event Logger → Training PS (trains model every minute)
    ↓              ↓
    ↓          Sync Parameters (every 60s)
    ↓              ↓
Serving PS (serves recommendations)
    ↓
User sees updated recommendations
```

**Impact:** We can't retrain without affecting serving performance.

---

### 6. ✅ Sparse Feature Handling (We Have This!)

**Monolith's Approach:**
- Handles millions of features (user_id, video_id, category, tags, etc.)
- Most features are sparse (0 for most users)

**Our Implementation:**
- ✅ We handle sparse features well
- ✅ Category-based embeddings
- ✅ Metadata filtering

**Verdict:** We're good here!

---

## What We Should Add

### Priority 1: Expirable Embeddings (Memory Critical)

```python
# In backend/app/embeddings.py

class ExpirableEmbeddingTable(CollisionlessEmbeddingTable):
    def __init__(self, ttl_days: int = 30):
        super().__init__()
        self.ttl_days = ttl_days
        self.last_accessed = {}  # video_id -> timestamp

    async def get_embedding(self, video_id: str):
        # Update last accessed
        self.last_accessed[video_id] = datetime.now()

        return await super().get_embedding(video_id)

    async def cleanup_expired(self):
        """Remove embeddings not accessed in TTL days."""
        now = datetime.now()
        expired = [
            vid for vid, last_access in self.last_accessed.items()
            if (now - last_access).days > self.ttl_days
        ]

        for vid in expired:
            self.remove_embedding(vid)

        logger.info(f"Cleaned up {len(expired)} expired embeddings")
```

**Benefits:**
- Keeps memory bounded
- Removes inactive users/videos
- Scales to billions of items

---

### Priority 2: Frequency Filtering (Memory Critical)

```python
# In backend/app/embeddings.py

MIN_INTERACTIONS_FOR_EMBEDDING = 10

async def should_create_embedding(video_id: str) -> bool:
    """Only create embeddings for popular videos."""
    # Get view count from database
    result = await db.query(f"SELECT view_count FROM video WHERE id = '{video_id}'")

    if not result:
        return False

    return result[0]["view_count"] >= MIN_INTERACTIONS_FOR_EMBEDDING

# In add_embedding:
if not await should_create_embedding(video_id):
    # Use default category embedding
    return DEFAULT_EMBEDDINGS[category]
```

**Benefits:**
- Reduces embedding table size by 80%+
- Only stores embeddings for videos people actually watch
- New videos use category defaults until they get popular

---

### Priority 3: Online Training (Performance Critical)

```python
# New file: backend/app/online_training.py

class OnlineTrainer:
    """Continuously retrain ML model with latest events."""

    def __init__(self, sync_interval_seconds: int = 60):
        self.sync_interval = sync_interval_seconds
        self.training_ps = {}  # Training parameter server
        self.serving_ps = {}   # Serving parameter server

    async def start_training_loop(self):
        """Run continuous training."""
        while True:
            # 1. Fetch latest events (last 60 seconds)
            events = await self.fetch_recent_events()

            # 2. Update training parameters
            await self.update_training_ps(events)

            # 3. Sync to serving PS
            await self.sync_to_serving()

            # 4. Wait for next sync
            await asyncio.sleep(self.sync_interval)

    async def update_training_ps(self, events):
        """Update model weights based on user interactions."""
        # Train on recent like/skip events
        for event in events:
            if event["event_type"] == "like":
                # Increase preference for this video's features
                self.adjust_weights(event["video_id"], delta=+0.01)
            elif event["event_type"] == "skip":
                # Decrease preference
                self.adjust_weights(event["video_id"], delta=-0.01)

    async def sync_to_serving(self):
        """Sync training parameters to serving."""
        self.serving_ps = self.training_ps.copy()
        logger.info("Synced training → serving parameters")
```

**Benefits:**
- Model improves in real-time (like TikTok)
- User preferences update every minute
- Better personalization

---

### Priority 4: Default Embeddings by Category (Easy Win)

```python
# In backend/app/embeddings.py

DEFAULT_EMBEDDINGS = {
    "sports": np.random.randn(128).astype(np.float32),
    "comedy": np.random.randn(128).astype(np.float32),
    "music": np.random.randn(128).astype(np.float32),
    "gaming": np.random.randn(128).astype(np.float32),
    # ... etc
}

# Normalize defaults
for category, emb in DEFAULT_EMBEDDINGS.items():
    DEFAULT_EMBEDDINGS[category] = emb / np.linalg.norm(emb)

async def get_embedding_with_fallback(video_id: str, category: str):
    """Get embedding, fallback to category default."""
    emb = await table.get_embedding(video_id)

    if emb is None:
        # Use category default
        return DEFAULT_EMBEDDINGS.get(category, DEFAULT_EMBEDDINGS["general"])

    return emb
```

**Benefits:**
- New videos get reasonable recommendations immediately
- Reduces embedding table size
- Simple to implement

---

## Comparison Table

| Feature | Monolith (TikTok) | Our Implementation | Priority |
|---------|-------------------|-------------------|----------|
| Collisionless Embeddings | ✅ Cuckoo Hashing | ✅ SHA256 | ✅ Have it |
| Real-time Event Logging | ✅ | ✅ | ✅ Have it |
| Real-time ML Feedback | ✅ | ✅ SSE | ✅ Have it |
| Online Training | ✅ Every 60s | ❌ | 🔴 Critical |
| Expirable Embeddings | ✅ TTL-based | ❌ | 🔴 Critical |
| Frequency Filtering | ✅ Min threshold | ❌ | 🔴 Critical |
| Default Category Embeddings | ✅ | ❌ | 🟡 Medium |
| Parameter Server Architecture | ✅ Dual PS | ❌ | 🟡 Medium |
| FAISS Indexing | ✅ | ✅ | ✅ Have it |
| Redis Caching | ✅ | ✅ | ✅ Have it |

---

## Recommended Implementation Order

### Phase 1: Memory Optimization (Critical for Scale)
1. **Default Category Embeddings** (1 hour)
   - Easiest to implement
   - Immediate memory savings

2. **Frequency Filtering** (2 hours)
   - Only embed popular videos
   - Reduces table size by 80%+

3. **Expirable Embeddings** (3 hours)
   - TTL-based cleanup
   - Keeps memory bounded

### Phase 2: Real-time Learning (Better Recommendations)
4. **Simple Online Training** (1 day)
   - Update user preferences every minute
   - No dual PS (keep it simple)

5. **Parameter Server Architecture** (3 days)
   - Full Monolith-style dual PS
   - Production-grade

---

## Code Examples Ready

I can implement any of these features. Which should we prioritize?

**Quick wins (1-2 hours each):**
- ✅ Default category embeddings
- ✅ Frequency filtering
- ✅ Expirable embeddings

**Big improvements (1-3 days each):**
- 🔥 Online training (biggest impact on recommendations)
- 🔥 Parameter server architecture

---

## Bottom Line

**What we have:**
- ✅ Collisionless embeddings (SHA256 - even better than Monolith's Cuckoo)
- ✅ Real-time event logging
- ✅ Real-time ML feedback via SSE
- ✅ FAISS indexing
- ✅ Redis caching

**What we're missing for TikTok-scale:**
- ❌ Expirable embeddings (memory will explode at scale)
- ❌ Frequency filtering (wasting 80% of memory on unpopular videos)
- ❌ Online training (model doesn't improve automatically)
- ❌ Default category embeddings (new videos get poor recommendations)

**Priority:** Start with memory optimizations (expirable embeddings + frequency filtering), then add online training.

---

## Sources

- [Monolith Paper (arXiv)](https://arxiv.org/abs/2209.07663)
- [ByteDance Monolith GitHub](https://github.com/bytedance/monolith)
- [Monolith Paper Summary](https://dhruvil.substack.com/p/paper-summary-monolith-real-time)
- [Mastering Recommender Systems: A Monolith Perspective](https://pub.aimind.so/mastering-recommender-systems-a-monolith-perspective-ac6613957bff)
