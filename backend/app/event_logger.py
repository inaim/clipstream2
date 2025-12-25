"""
Event Logger

Logs user interaction events and updates video/user statistics in real-time.

This module handles all event tracking including:
- Video plays/pauses/completions/skips
- Likes/unlikes
- Rewatches
- Video stats aggregation
- User interest profile updates
"""

import time
import logging
from typing import Dict, Any, Optional
from surrealdb import AsyncSurreal

logger = logging.getLogger(__name__)


async def log_event(db: AsyncSurreal, event: Dict[str, Any]) -> bool:
    """
    Log a user interaction event and update related statistics.

    Expected event format:
    {
        "user_id": "user:123",
        "video_id": "video:456",
        "event_type": "play_end" | "skip" | "like" | "rewatch" | "share" | "comment",
        "timestamp": 1234567890.0,
        "watch_ratio": 0.75,  # % of video watched (0.0 - 1.0)
        "category": "sports",  # video category
        "metadata": {...}  # optional extra data
    }

    Args:
        db: Connected SurrealDB instance
        event: Event data dictionary

    Returns:
        bool: True if event logged successfully
    """
    try:
        # Insert raw event into events table
        await db.create("event", event)
        logger.debug(f"Logged event: {event['event_type']} for video {event['video_id']}")

        # Update video statistics
        await update_video_stats(db, event)

        # Update user statistics
        await update_user_stats(db, event)

        return True

    except Exception as e:
        logger.error(f"Failed to log event: {e}")
        return False


async def update_video_stats(db: AsyncSurreal, event: Dict[str, Any]):
    """
    Update video statistics based on event.

    This updates:
    - Impressions count
    - Total watch ratio (cumulative)
    - Completion count
    - Early skip count
    - Like count
    - Rewatch count
    - Share count
    - Last seen timestamp

    Args:
        db: Connected SurrealDB instance
        event: Event data dictionary
    """
    video_id = event["video_id"]
    event_type = event["event_type"]
    watch_ratio = event.get("watch_ratio", 0.0)
    timestamp = event.get("timestamp", time.time())

    # Get current video stats
    video_result = await db.query(f"SELECT * FROM {video_id}")
    if not video_result or len(video_result) == 0 or not video_result[0].get("result"):
        logger.warning(f"Video {video_id} not found for stats update")
        return

    video = video_result[0]["result"][0]
    stats = video.get("stats", {})

    # Update stats based on event type
    if event_type in ("play_end", "skip"):
        # Increment impressions and update watch ratio
        stats["impressions"] = stats.get("impressions", 0) + 1
        stats["total_watch_ratio"] = stats.get("total_watch_ratio", 0.0) + watch_ratio

        # Completion detection (watched >= 80%)
        if watch_ratio >= 0.8:
            stats["completions"] = stats.get("completions", 0) + 1

        # Early skip detection (watched <= 20%)
        if watch_ratio <= 0.2:
            stats["early_skips"] = stats.get("early_skips", 0) + 1

        # Update last seen timestamp
        await db.query(
            f"UPDATE {video_id} SET last_seen_ts = {timestamp}, stats = {stats}"
        )

    elif event_type == "like":
        stats["likes"] = stats.get("likes", 0) + 1
        await db.query(f"UPDATE {video_id} SET stats = {stats}")

    elif event_type == "unlike":
        stats["likes"] = max(0, stats.get("likes", 0) - 1)
        await db.query(f"UPDATE {video_id} SET stats = {stats}")

    elif event_type == "rewatch":
        stats["rewatches"] = stats.get("rewatches", 0) + 1
        await db.query(f"UPDATE {video_id} SET stats = {stats}")

    elif event_type == "share":
        stats["shares"] = stats.get("shares", 0) + 1
        await db.query(f"UPDATE {video_id} SET stats = {stats}")

    elif event_type == "comment":
        stats["comments"] = stats.get("comments", 0) + 1
        await db.query(f"UPDATE {video_id} SET stats = {stats}")

    logger.debug(f"Updated video stats for {video_id}: {stats}")


async def update_user_stats(db: AsyncSurreal, event: Dict[str, Any]):
    """
    Update user interest profile based on event.

    This updates:
    - Category-specific stats (impressions, watch ratio, likes per category)
    - Total events count
    - Video history (per-video impression counts)

    Args:
        db: Connected SurrealDB instance
        event: Event data dictionary
    """
    user_id = event["user_id"]
    video_id = event["video_id"]
    category = event.get("category", "unknown")
    watch_ratio = event.get("watch_ratio", 0.0)
    event_type = event["event_type"]

    # Get current user stats
    user_result = await db.query(f"SELECT * FROM {user_id}")
    if not user_result or len(user_result) == 0 or not user_result[0].get("result"):
        logger.warning(f"User {user_id} not found for stats update")
        return

    user = user_result[0]["result"][0]

    # Initialize stats structures if needed
    category_stats = user.get("category_stats", {})
    if category not in category_stats:
        category_stats[category] = {
            "impressions": 0,
            "watch_ratio": 0.0,
            "likes": 0,
        }

    video_history = user.get("video_history", {})
    total_events = user.get("total_events", 0)

    # Update category stats
    if event_type in ("play_end", "skip"):
        category_stats[category]["impressions"] += 1
        category_stats[category]["watch_ratio"] += watch_ratio

    if event_type == "like":
        category_stats[category]["likes"] = category_stats[category].get("likes", 0) + 1

    # Update video history (per-video impression count)
    video_history[video_id] = video_history.get(video_id, 0) + 1

    # Increment total events
    total_events += 1

    # Update user document
    await db.query(
        f"UPDATE {user_id} SET category_stats = {category_stats}, "
        f"video_history = {video_history}, total_events = {total_events}"
    )

    logger.debug(f"Updated user stats for {user_id}: category={category}, total_events={total_events}")


async def batch_log_events(db: AsyncSurreal, events: list) -> Dict[str, Any]:
    """
    Log multiple events in batch for better performance.

    Args:
        db: Connected SurrealDB instance
        events: List of event dictionaries

    Returns:
        dict: Batch processing results
    """
    results = {
        "total": len(events),
        "success": 0,
        "failed": 0,
        "errors": []
    }

    for event in events:
        try:
            success = await log_event(db, event)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "event": event,
                "error": str(e)
            })

    logger.info(f"Batch logged {results['success']}/{results['total']} events")
    return results


async def get_video_analytics(db: AsyncSurreal, video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed analytics for a video.

    Args:
        db: Connected SurrealDB instance
        video_id: Video ID (e.g., "video:123")

    Returns:
        dict: Analytics summary or None if video not found
    """
    try:
        result = await db.query(f"SELECT * FROM {video_id}")
        if not result or len(result) == 0 or not result[0].get("result"):
            return None

        video = result[0]["result"][0]
        stats = video.get("stats", {})
        impressions = stats.get("impressions", 0)

        if impressions == 0:
            return {
                "video_id": video_id,
                "title": video.get("title", "Untitled"),
                "impressions": 0,
                "message": "No analytics data yet"
            }

        # Calculate derived metrics
        avg_watch_ratio = stats.get("total_watch_ratio", 0.0) / impressions
        completion_rate = stats.get("completions", 0) / impressions
        like_rate = stats.get("likes", 0) / impressions
        skip_rate = stats.get("early_skips", 0) / impressions
        rewatch_rate = stats.get("rewatches", 0) / impressions

        return {
            "video_id": video_id,
            "title": video.get("title", "Untitled"),
            "category": video.get("category", "unknown"),
            "impressions": impressions,
            "avg_watch_ratio": round(avg_watch_ratio, 3),
            "completion_rate": round(completion_rate, 3),
            "like_rate": round(like_rate, 3),
            "skip_rate": round(skip_rate, 3),
            "rewatch_rate": round(rewatch_rate, 3),
            "raw_stats": stats,
            "created_at": video.get("created_at"),
            "last_seen_ts": video.get("last_seen_ts"),
        }

    except Exception as e:
        logger.error(f"Failed to get video analytics: {e}")
        return None


async def get_user_analytics(db: AsyncSurreal, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed analytics for a user.

    Args:
        db: Connected SurrealDB instance
        user_id: User ID (e.g., "user:123")

    Returns:
        dict: Analytics summary or None if user not found
    """
    try:
        result = await db.query(f"SELECT * FROM {user_id}")
        if not result or len(result) == 0 or not result[0].get("result"):
            return None

        user = result[0]["result"][0]
        category_stats = user.get("category_stats", {})
        total_events = user.get("total_events", 0)

        # Calculate category preferences
        category_preferences = {}
        for category, stats in category_stats.items():
            impressions = stats.get("impressions", 0)
            if impressions > 0:
                avg_watch = stats.get("watch_ratio", 0.0) / impressions
                like_rate = stats.get("likes", 0) / impressions

                category_preferences[category] = {
                    "impressions": impressions,
                    "avg_watch_ratio": round(avg_watch, 3),
                    "like_rate": round(like_rate, 3),
                }

        return {
            "user_id": user_id,
            "email": user.get("email", "unknown"),
            "total_events": total_events,
            "category_preferences": category_preferences,
            "unique_videos_watched": len(user.get("video_history", {})),
        }

    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        return None
