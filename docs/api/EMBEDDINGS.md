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

See full documentation in `docs/guides/EMBEDDINGS.md`
