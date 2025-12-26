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
