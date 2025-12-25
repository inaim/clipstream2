# 🤖 Real-time ML Guide

Complete guide to real-time ML feedback system.

See full documentation in: `../TIKTOK_REALTIME_GUIDE.md`

## Quick Overview

- SSE for instant feedback
- Redis Pub/Sub for broadcasting
- Event buffering for high volume
- ML updates in ~100ms

## Architecture

```
User Swipes → Event Logged → ML Updates →
SSE Publishes → Frontend Receives → UI Updates
```

Performance: ~100ms end-to-end
