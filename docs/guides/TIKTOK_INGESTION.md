# 🎬 TikTok Video Ingestion

Download and ingest real TikTok videos.

## Setup

```bash
pip install yt-dlp
```

## Create Ingestion Script

```python
import asyncio
from app.tiktok_scraper import download_and_prepare_tiktok_videos
from app.ingestion_engine import ingest_initial_videos
from db.surrealdb_client import db_client

async def ingest_tiktoks():
    await db_client.connect()
    async_db = getattr(db_client, "async_db")

    urls = [
        "https://www.tiktok.com/@nike/video/...",
        "https://www.tiktok.com/@espn/video/...",
    ]

    videos = await download_and_prepare_tiktok_videos(urls)
    result = await ingest_initial_videos(async_db, videos)

    print(f"Ingested {result['ingested']} videos")

asyncio.run(ingest_tiktoks())
```

## Run

```bash
python3 ingest_tiktok.py
```

See full guide in TIKTOK_REALTIME_GUIDE.md
