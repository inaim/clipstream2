# ⚡ Real-time Events API

Server-Sent Events (SSE) for real-time ML feedback.

## Subscribe to ML Feedback

```javascript
const eventSource = new EventSource(
  'http://localhost:8080/api/v1/realtime/stream/ml-feedback?user_id=user:test1'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('ML Update:', data.feedback);
};
```

## Log Event

```bash
POST /api/v1/realtime/stream/event
{
  "user_id": "user:test1",
  "video_id": "video:5",
  "event_type": "like",
  "watch_ratio": 0.85,
  "category": "sports"
}
```

See full documentation in TIKTOK_REALTIME_GUIDE.md
