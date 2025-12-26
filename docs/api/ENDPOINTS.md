<!--
Version: v20251226
Last-updated: 2025-12-26
Status: canonical
-->

# 📡 API Endpoints Reference

Complete API reference for Clipstream.

## Infinite Feed

```
POST /api/v1/infinite/infinite         - Get infinite scroll feed
POST /api/v1/infinite/events/batch     - Batch event logging
GET  /api/v1/infinite/prefetch         - Prefetch next batch
POST /api/v1/infinite/refresh          - Refresh feed
GET  /api/v1/infinite/analytics/feed-quality - Feed metrics
```

## Real-time Events

```
GET  /api/v1/realtime/stream/ml-feedback - SSE stream
POST /api/v1/realtime/stream/event     - Log event with feedback
POST /api/v1/realtime/stream/event/buffered - Buffered logging
```

## Embeddings

```
POST /api/v1/embeddings/add            - Add embedding
POST /api/v1/embeddings/batch          - Batch add
POST /api/v1/embeddings/search         - Search similar
GET  /api/v1/embeddings/similar/{id}   - Get similar videos
GET  /api/v1/embeddings/get/{id}       - Get embedding
DELETE /api/v1/embeddings/remove/{id}  - Remove embedding
GET  /api/v1/embeddings/stats          - Get stats
POST /api/v1/embeddings/generate-dummy - Generate test data
```

## Authentication

```
POST /api/v1/auth/register             - Register user
POST /api/v1/auth/login                - Login
GET  /api/v1/auth/me                   - Get current user
```

## Analytics

```
GET /api/v1/events/analytics/user/{id}  - User analytics
GET /api/v1/events/analytics/video/{id} - Video analytics
```

See detailed examples in original guides.
