"""
Video Ingestion Engine

Automatically pulls videos from various sources, extracts metadata,
generates embeddings, and saves them to SurrealDB.

This engine runs at startup to populate the initial video catalog
and can be triggered on-demand for continuous ingestion.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from surrealdb import AsyncSurreal

logger = logging.getLogger(__name__)


async def ingest_initial_videos(db: AsyncSurreal, video_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingest a batch of videos into the database.

    Expected video_sources format:
    [
        {
            "url": "https://cdn.example.com/video1.mp4",
            "category": "sports",
            "duration": 12.4,
            "embedding": [0.12, -0.33, 0.55, ...],
            "title": "Amazing Basketball Shot",
            "creator_id": "user:123",  # optional
            "tags": ["sports", "basketball"],  # optional
        },
        ...
    ]

    Args:
        db: Connected SurrealDB instance
        video_sources: List of video metadata dictionaries

    Returns:
        dict: Ingestion results with counts and any errors
    """
    results = {
        "total": len(video_sources),
        "ingested": 0,
        "skipped": 0,
        "errors": []
    }

    logger.info(f"Starting ingestion of {results['total']} videos...")

    for idx, video_data in enumerate(video_sources, 1):
        try:
            await ingest_single_video(db, video_data)
            results["ingested"] += 1
            logger.info(f"✓ Ingested video {idx}/{results['total']}: {video_data.get('url', 'unknown')}")

        except Exception as e:
            results["errors"].append({
                "video": video_data.get("url", f"index_{idx}"),
                "error": str(e)
            })
            results["skipped"] += 1
            logger.error(f"✗ Failed to ingest video {idx}/{results['total']}: {e}")

    logger.info(
        f"Ingestion complete: {results['ingested']} ingested, "
        f"{results['skipped']} skipped, {len(results['errors'])} errors"
    )

    return results


async def ingest_single_video(db: AsyncSurreal, video_data: Dict[str, Any]) -> str:
    """
    Ingest a single video into the database.

    Args:
        db: Connected SurrealDB instance
        video_data: Video metadata dictionary

    Returns:
        str: Video ID of the created record

    Raises:
        ValueError: If required fields are missing
    """
    # Validate required fields
    required_fields = ["url", "category", "duration"]
    for field in required_fields:
        if field not in video_data:
            raise ValueError(f"Missing required field: {field}")

    # Build video document with defaults
    current_time = time.time()

    video_doc = {
        # Core metadata
        "url": video_data["url"],
        "cdn_url": video_data.get("cdn_url", video_data["url"]),  # fallback to url
        "category": video_data["category"],
        "duration": video_data["duration"],
        "title": video_data.get("title", "Untitled Video"),

        # Creator info
        "creator_id": video_data.get("creator_id", "user:system"),

        # Embeddings for ML
        "embedding": video_data.get("embedding", []),

        # Tags and metadata
        "tags": video_data.get("tags", []),
        "hashtags": video_data.get("hashtags", []),
        "description": video_data.get("description", ""),

        # Timestamps
        "created_at": current_time,
        "last_seen_ts": 0,  # never shown yet

        # Status
        "status": video_data.get("status", "active"),  # active, processing, queued, deleted

        # Statistics (initialized to zero)
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

        # View/engagement metrics
        "view_count": video_data.get("view_count", 0),
        "like_count": video_data.get("like_count", 0),

        # Video file metadata
        "filename": video_data.get("filename", ""),
        "file_size": video_data.get("file_size", 0),
        "content_hash": video_data.get("content_hash", ""),

        # Processing metadata
        "processing_steps": video_data.get("processing_steps", {}),

        # Moderation
        "moderation_status": video_data.get("moderation_status", "approved"),
    }

    # Create video in database
    result = await db.create("video", video_doc)

    # Extract video ID from result
    video_id = None
    if isinstance(result, list) and len(result) > 0:
        video_id = result[0].get("id", "unknown")
    elif isinstance(result, dict):
        video_id = result.get("id", "unknown")

    logger.debug(f"Created video: {video_id}")
    return video_id


async def ingest_from_tiktok_urls(db: AsyncSurreal, tiktok_urls: List[str]) -> Dict[str, Any]:
    """
    Ingest videos from TikTok URLs.

    This is a placeholder for TikTok scraping/downloading logic.
    In production, this would:
    1. Download video from TikTok
    2. Extract metadata (title, creator, views, etc.)
    3. Generate embeddings
    4. Save to CDN
    5. Insert into database

    Args:
        db: Connected SurrealDB instance
        tiktok_urls: List of TikTok video URLs

    Returns:
        dict: Ingestion results
    """
    logger.warning("TikTok ingestion not yet implemented - placeholder only")

    # Placeholder implementation
    video_sources = []
    for url in tiktok_urls:
        video_sources.append({
            "url": url,
            "category": "tiktok",
            "duration": 15.0,
            "embedding": [0.0] * 128,  # placeholder embedding
            "title": f"TikTok Video - {url}",
            "status": "queued",  # needs processing
        })

    return await ingest_initial_videos(db, video_sources)


async def ingest_from_uploads(db: AsyncSurreal, upload_dir: str) -> Dict[str, Any]:
    """
    Ingest videos from local upload directory.

    Scans upload directory for new video files and processes them.

    Args:
        db: Connected SurrealDB instance
        upload_dir: Path to upload directory

    Returns:
        dict: Ingestion results
    """
    import os
    from pathlib import Path

    logger.info(f"Scanning upload directory: {upload_dir}")

    video_extensions = {".mp4", ".webm", ".mov", ".avi"}
    video_sources = []

    upload_path = Path(upload_dir)
    if not upload_path.exists():
        logger.warning(f"Upload directory does not exist: {upload_dir}")
        return {"total": 0, "ingested": 0, "skipped": 0, "errors": []}

    for video_file in upload_path.iterdir():
        if video_file.suffix.lower() in video_extensions:
            # Get file metadata
            stat = video_file.stat()

            video_sources.append({
                "url": f"/uploads/{video_file.name}",
                "cdn_url": f"/uploads/{video_file.name}",
                "category": "upload",
                "duration": 10.0,  # TODO: extract actual duration with ffmpeg
                "embedding": [],  # TODO: generate embedding
                "title": video_file.stem.replace("_", " ").replace("-", " ").title(),
                "filename": video_file.name,
                "file_size": stat.st_size,
                "status": "queued",
            })

    logger.info(f"Found {len(video_sources)} videos in upload directory")
    return await ingest_initial_videos(db, video_sources)


async def generate_demo_videos(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate demo videos for testing and development.

    Args:
        count: Number of demo videos to generate

    Returns:
        list: List of video metadata dictionaries
    """
    import random

    categories = ["sports", "comedy", "music", "gaming", "education", "food", "travel"]
    demo_videos = []

    demo_base = os.getenv("DEMO_VIDEO_BASE_URL", "http://localhost:8080")
    demo_base = demo_base.rstrip("/")

    for i in range(count):
        category = random.choice(categories)
        duration = random.uniform(5.0, 30.0)

        # Generate random embedding (128-dimensional)
        embedding = [random.uniform(-1.0, 1.0) for _ in range(128)]

        demo_videos.append({
            "url": f"{demo_base}/uploads/demo/video_{i+1}.mp4",
            "cdn_url": f"{demo_base}/uploads/demo/video_{i+1}.mp4",
            "category": category,
            "duration": round(duration, 2),
            "embedding": embedding,
            "title": f"Demo {category.title()} Video #{i+1}",
            "tags": [category, "demo", "test"],
            "creator_id": "user:system",
            "status": "active",
        })

    return demo_videos


async def continuous_ingestion_loop(db: AsyncSurreal, interval_seconds: int = 300):
    """
    Continuously monitor for new videos and ingest them.

    This function runs in the background and periodically checks
    for new content to ingest.

    Args:
        db: Connected SurrealDB instance
        interval_seconds: How often to check for new content (default 5 minutes)
    """
    import asyncio

    logger.info(f"Starting continuous ingestion loop (interval: {interval_seconds}s)")

    while True:
        try:
            # TODO: Implement your ingestion sources
            # - Monitor upload directory
            # - Poll TikTok API
            # - Check RSS feeds
            # - Watch S3/GCS buckets
            # etc.

            logger.debug("Checking for new videos to ingest...")
            await asyncio.sleep(interval_seconds)

        except Exception as e:
            logger.error(f"Error in continuous ingestion loop: {e}")
            await asyncio.sleep(interval_seconds)
