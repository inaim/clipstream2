# 🏗️ System Architecture

High-level architecture of Clipstream platform.

## Components

```
┌─────────────────────────────────────────────┐
│         Frontend (Swipe UI)                 │
│  - TikTok-style gestures                    │
│  - Infinite scroll                          │
│  - Real-time ML feedback                    │
└──────────────┬──────────────────────────────┘
               │ HTTP/SSE
┌──────────────▼──────────────────────────────┐
│           Backend APIs                       │
│  - Infinite Feed API                        │
│  - Real-time Events API                     │
│  - Embeddings API                           │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│         Storage & ML Layer                   │
│  - SurrealDB (metadata)                     │
│  - Redis (pub/sub)                          │
│  - FAISS (embeddings)                       │
│  - ML Algorithm (ranking)                   │
└──────────────────────────────────────────────┘
```

See detailed architecture in original docs.
