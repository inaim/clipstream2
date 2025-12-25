"""
Seed Real Playable Videos for Testing

This script adds real, playable videos to your platform so you can test:
- Swiping on videos in the frontend
- ML algorithm learning from interactions
- Different user preferences

Uses public demo videos that work in browsers.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from surrealdb import AsyncSurreal
from utils.config import settings
import random

# Real playable videos (public CDN, works in browsers)
REAL_VIDEOS = [
    # Sports
    {
        "title": "Basketball Highlights",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "category": "sports",
        "duration": 596.5,
        "description": "Amazing basketball plays and dunks",
        "tags": ["sports", "basketball", "highlights"],
    },
    {
        "title": "Soccer Goals Compilation",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "category": "sports",
        "duration": 653.8,
        "description": "Best soccer goals of the season",
        "tags": ["sports", "soccer", "goals"],
    },
    # Comedy
    {
        "title": "Funny Animals",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "category": "comedy",
        "duration": 15.0,
        "description": "Hilarious animal moments",
        "tags": ["comedy", "animals", "funny"],
    },
    {
        "title": "Epic Fails",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "category": "comedy",
        "duration": 15.0,
        "description": "Epic fail compilation",
        "tags": ["comedy", "fails", "viral"],
    },
    # Music
    {
        "title": "Guitar Solo",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "category": "music",
        "duration": 60.0,
        "description": "Amazing guitar performance",
        "tags": ["music", "guitar", "rock"],
    },
    {
        "title": "Dance Performance",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
        "category": "music",
        "duration": 15.0,
        "description": "Epic dance moves",
        "tags": ["music", "dance", "performance"],
    },
    # Gaming
    {
        "title": "Gaming Highlights",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
        "category": "gaming",
        "duration": 15.0,
        "description": "Best gaming moments",
        "tags": ["gaming", "highlights", "esports"],
    },
    {
        "title": "Speedrun Record",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
        "category": "gaming",
        "duration": 888.0,
        "description": "World record speedrun",
        "tags": ["gaming", "speedrun", "record"],
    },
    # Education
    {
        "title": "How Things Work",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4",
        "category": "education",
        "duration": 30.0,
        "description": "Educational content",
        "tags": ["education", "learning", "science"],
    },
    {
        "title": "Quick Science Fact",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
        "category": "education",
        "duration": 734.0,
        "description": "Interesting science facts",
        "tags": ["education", "science", "facts"],
    },
    # Food
    {
        "title": "Quick Recipe",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/VolkswagenGTIReview.mp4",
        "category": "food",
        "duration": 20.0,
        "description": "Easy cooking tutorial",
        "tags": ["food", "recipe", "cooking"],
    },
    {
        "title": "Food Review",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
        "category": "food",
        "duration": 25.0,
        "description": "Restaurant food review",
        "tags": ["food", "review", "restaurant"],
    },
    # Travel
    {
        "title": "Travel Vlog",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WhatCarCanYouGetForAGrand.mp4",
        "category": "travel",
        "duration": 30.0,
        "description": "Beautiful travel destinations",
        "tags": ["travel", "vlog", "adventure"],
    },
]


async def seed_videos():
    """
    Seed real playable videos into the database.
    """
    print("🎬 Seeding Real Playable Videos")
    print("=" * 60)

    # Connect to SurrealDB
    db = AsyncSurreal(settings.SURREALDB_URL)
    await db.connect()

    # Authenticate
    if settings.ENVIRONMENT == "production":
        await db.signin({
            "username": settings.SURREALDB_USER,
            "password": settings.SURREALDB_PASS,
            "namespace": settings.SURREALDB_NS
        })
    else:
        await db.signin({
            "username": settings.SURREALDB_USER,
            "password": settings.SURREALDB_PASS,
        })

    await db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
    print(f"✅ Connected to SurrealDB")

    # Seed videos
    created_count = 0
    for video_data in REAL_VIDEOS:
        try:
            # Generate random embedding (128-dimensional)
            embedding = [random.uniform(-1.0, 1.0) for _ in range(128)]

            # Create video document
            video = {
                "url": video_data["cdn_url"],
                "cdn_url": video_data["cdn_url"],
                "title": video_data["title"],
                "category": video_data["category"],
                "duration": video_data["duration"],
                "description": video_data.get("description", ""),
                "tags": video_data.get("tags", []),
                "embedding": embedding,
                "creator_id": "user:system",
                "status": "active",
                "created_at": asyncio.get_event_loop().time(),
                "last_seen_ts": 0,
                "stats": {
                    "impressions": 0,
                    "total_watch_ratio": 0.0,
                    "completions": 0,
                    "early_skips": 0,
                    "likes": 0,
                    "rewatches": 0,
                    "shares": 0,
                    "comments": 0,
                },
                "view_count": 0,
                "like_count": 0,
                "filename": f"{video_data['title'].replace(' ', '_')}.mp4",
                "file_size": 0,
                "content_hash": "",
                "processing_steps": {},
                "moderation_status": "approved",
            }

            # Insert into database
            result = await db.create("video", video)
            created_count += 1
            print(f"✅ Added: {video_data['title']} ({video_data['category']})")

        except Exception as e:
            print(f"❌ Failed to add {video_data['title']}: {e}")

    print("=" * 60)
    print(f"🎉 Seeded {created_count}/{len(REAL_VIDEOS)} videos!")
    print("")
    print("📺 Your platform now has REAL playable videos!")
    print("")
    print("Next steps:")
    print("1. Start backend: cd backend && python3 main.py")
    print("2. Test feed: curl http://localhost:8080/api/v1/feed/for-you?limit=10")
    print("3. Open frontend and start swiping!")
    print("")
    print("Categories available:")
    categories = set(v["category"] for v in REAL_VIDEOS)
    for cat in sorted(categories):
        count = len([v for v in REAL_VIDEOS if v["category"] == cat])
        print(f"  - {cat}: {count} videos")

    await db.close()


if __name__ == "__main__":
    asyncio.run(seed_videos())
