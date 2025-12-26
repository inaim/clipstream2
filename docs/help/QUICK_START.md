<!--
Version: v20251226
Last-updated: 2025-12-26
Status: canonical
-->

# 🚀 Quick Start Guide

Get Clipstream running in 5 minutes.

---

## Prerequisites

- Docker & Docker Compose
- Python 3.8+
- Redis (via Docker)
- SurrealDB (via Docker)

---

## 1. Start Platform (1 Command)

```bash
cd ~/Documents/projects/clipstream
bash START_TIKTOK_PLATFORM.sh
```

**What happens:**
1. ✅ Docker starts SurrealDB & Redis
2. ✅ Backend initializes database
3. ✅ 13 real videos ingested
4. ✅ ML algorithm ready
5. ✅ Platform running on port 8080

**Expected output:**
```
✅ Phase 1: SurrealDB Connected
✅ Phase 2: Schema Ready (9 tables)
✅ Phase 3: Ingestion Complete
   - Ingested: 13 videos
✅ Phase 4: Platform Ready
```

---

## 2. Test Swipe Interface

**Open in browser:**
```bash
python3 -m http.server 8000
open http://localhost:8000/frontend_tiktok_swipe.html
```

**What you'll see:**
- ✅ Real videos playing
- ✅ Swipe up = Like (❤️)
- ✅ Swipe down = Skip (⏭️)
- ✅ ML panel showing preferences
- ✅ Green dot = Connected to ML stream

---

## 3. Test API

```bash
# Check health
curl http://localhost:8080/api/v1/embeddings/stats | jq

# Generate embeddings
curl -X POST "http://localhost:8080/api/v1/embeddings/generate-dummy?count=1000" | jq

# Search similar videos
curl "http://localhost:8080/api/v1/embeddings/similar/video:5?k=10" | jq
```

---

## 4. Test Real-time ML

```bash
# Create user
USER=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","display_name":"Test"}' | jq -r '.id')

# Like sports videos
curl -X POST http://localhost:8080/api/v1/realtime/stream/event \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER\",\"video_id\":\"video:1\",\"event_type\":\"like\",\"watch_ratio\":0.9,\"category\":\"sports\"}"

# Get personalized feed
curl -X POST http://localhost:8080/api/v1/infinite/infinite \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER\",\"cursor\":null,\"limit\":5}" | jq
```

**Expected:** Feed shows MORE sports videos

---

## 5. Monitor System

```bash
# Embedding stats
curl http://localhost:8080/api/v1/embeddings/stats | jq

# Feed quality
curl "http://localhost:8080/api/v1/infinite/analytics/feed-quality?user_id=$USER" | jq

# User analytics
curl "http://localhost:8080/api/v1/events/analytics/user/$USER" | jq
```

---

## Next Steps

- **Add real TikTok videos:** See [`guides/TIKTOK_INGESTION.md`](../guides/TIKTOK_INGESTION.md)
- **Scale to production:** See [`architecture/SCALING.md`](../architecture/SCALING.md)
- **Test ML algorithm:** See [`TESTING.md`](TESTING.md)
- **Deploy:** See deployment guide

---

## Troubleshooting

### Backend won't start
```bash
# Check Docker
docker ps

# Restart services
docker-compose restart surrealdb redis
```

### Videos not playing
```bash
# Check video URLs
curl http://localhost:8080/api/v1/feed/for-you?limit=1 | jq '.[0].cdn_url'

# Should see Google CDN URLs
```

### SSE not connecting
```bash
# Check Redis
redis-cli ping

# Test SSE manually
curl -N http://localhost:8080/api/v1/realtime/stream/ml-feedback?user_id=user:test1
```

---

**That's it! Platform is running.** 🎉

For more details, see:
- [`api/ENDPOINTS.md`](../api/ENDPOINTS.md) - API reference
- [`architecture/OVERVIEW.md`](../architecture/OVERVIEW.md) - Architecture
- [`TESTING.md`](TESTING.md) - Testing guide
