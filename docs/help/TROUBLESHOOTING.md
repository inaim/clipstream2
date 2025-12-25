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
