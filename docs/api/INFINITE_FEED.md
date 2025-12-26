# ∞ Infinite Scroll Feed API

Cursor-based pagination for infinite scroll.

## Get Feed

```bash
POST /api/v1/infinite/infinite
{
  "user_id": "user:test1",
  "cursor": null,
  "limit": 10,
  "exclude_seen": true
}
```

## Response

```json
{
  "videos": [...],
  "next_cursor": "video:10",
  "has_more": true,
  "total_candidates": 50,
  "personalization_score": 0.735
}
```

See full documentation in TIKTOK_REALTIME_GUIDE.md
