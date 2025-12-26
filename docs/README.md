# 📚 Clipstream Documentation

Complete documentation for the Clipstream TikTok-style video platform.

---

## 🚀 Quick Start

**Start here:** [`help/QUICK_START.md`](help/QUICK_START.md)

One command to get everything running:
```bash
bash START_TIKTOK_PLATFORM.sh
```

---

## 📖 Documentation Structure

### 🎯 Help & Guides
- [`help/QUICK_START.md`](help/QUICK_START.md) - Get started in 5 minutes
- [`help/TESTING.md`](help/TESTING.md) - Testing guide for all features
- [`guides/EMBEDDINGS.md`](guides/EMBEDDINGS.md) - Collision-less embeddings
- [`guides/TIKTOK_INGESTION.md`](guides/TIKTOK_INGESTION.md) - TikTok video scraping
- [`guides/REALTIME_ML.md`](guides/REALTIME_ML.md) - Real-time ML feedback

### 🏗️ Architecture
- [`architecture/OVERVIEW.md`](architecture/OVERVIEW.md) - System architecture
- [`architecture/ML_ALGORITHM.md`](architecture/ML_ALGORITHM.md) - ML ranking algorithm
- [`architecture/DATABASE_SCHEMA.md`](architecture/DATABASE_SCHEMA.md) - Database design
- [`architecture/SCALING.md`](architecture/SCALING.md) - Scaling to TikTok level

### 🔌 API Reference
- [`api/ENDPOINTS.md`](api/ENDPOINTS.md) - All API endpoints
- [`api/INFINITE_FEED.md`](api/INFINITE_FEED.md) - Infinite scroll API
- [`api/REALTIME_EVENTS.md`](api/REALTIME_EVENTS.md) - SSE & event streaming
- [`api/EMBEDDINGS.md`](api/EMBEDDINGS.md) - Embedding similarity API

---

## 🎯 Common Tasks

### For Developers
```bash
# Start development environment
bash START_TIKTOK_PLATFORM.sh

# Run tests
bash TEST_NOW.sh

# Generate embeddings
curl -X POST "http://localhost:8080/api/v1/embeddings/generate-dummy?count=1000"
```

### For Testing
```bash
# Test swipe interface
open http://localhost:8000/frontend_tiktok_swipe.html

# Test ML personalization
see docs/help/TESTING.md

# Check system health
curl http://localhost:8080/api/v1/embeddings/stats
```

### For Deployment
```bash
# See architecture/SCALING.md for production deployment
# See guides/TIKTOK_INGESTION.md for real video ingestion
```

---

## 🤖 RAG Knowledge Base

This documentation is optimized for RAG (Retrieval-Augmented Generation) chatbots.

**Vector Database Schema:**
```json
{
  "doc_id": "quick_start",
  "category": "help",
  "title": "Quick Start Guide",
  "content": "...",
  "keywords": ["setup", "install", "start", "quick"],
  "embedding": [0.123, 0.456, ...]
}
```

**See:** [`RAG_INDEX.json`](RAG_INDEX.json) for full searchable index.

---

## 📊 Feature Overview

| Feature | Status | Documentation |
|---------|--------|---------------|
| TikTok Video Scraper | ✅ | [`guides/TIKTOK_INGESTION.md`](guides/TIKTOK_INGESTION.md) |
| Swipe Interface | ✅ | [`help/QUICK_START.md`](help/QUICK_START.md) |
| Real-time ML | ✅ | [`guides/REALTIME_ML.md`](guides/REALTIME_ML.md) |
| Infinite Scroll | ✅ | [`api/INFINITE_FEED.md`](api/INFINITE_FEED.md) |
| Collision-less Embeddings | ✅ | [`guides/EMBEDDINGS.md`](guides/EMBEDDINGS.md) |
| Event Buffering | ✅ | [`architecture/SCALING.md`](architecture/SCALING.md) |

---

## 🆘 Troubleshooting

See [`help/TROUBLESHOOTING.md`](help/TROUBLESHOOTING.md) for common issues.

**Quick fixes:**
- Redis not running? `docker-compose up -d redis`
- Videos not loading? Check `backend/.env.production`
- SSE not working? Check CORS settings

---

## 📞 Support

- **Issues:** See troubleshooting guide
- **Questions:** Check API reference
- **Chatbot:** Use RAG_INDEX.json for context-aware help

---

**Last Updated:** 2024-12-25
**Version:** 1.0.0
**Platform:** Clipstream TikTok-style Video Platform
