"""
Video Event Recording System

Records all user interactions with videos for training the AI recommendation model.
Events include:
- Views (impressions, watch time, completion rate)
- Engagement (likes, comments, shares)
- Negative signals (skips, quick scrolls, dismissals)
- Virality signals (rapid growth in views/shares)

These events are stored in SurrealDB and used to train the scoring model.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging
from enum import Enum

logger = logging.getLogger(__name__)


def normalize_id(record_id: Union[str, Dict], table_prefix: str = "") -> str:
    """
    Normalize SurrealDB record ID to just the ID part.

    SurrealDB can return IDs in different formats:
    - String: "video:123" or "123"
    - Dict: {"table_name": "video", "id": "123"}

    Args:
        record_id: Record ID in any format
        table_prefix: Expected table prefix (e.g., "videos:", "users:")

    Returns:
        id_part: Just the ID part without table prefix
    """
    if isinstance(record_id, dict):
        # Dict format: {"table_name": "video", "id": "123"}
        return str(record_id.get("id", ""))
    elif isinstance(record_id, str):
        # String format: "video:123" or "123"
        if table_prefix and record_id.startswith(table_prefix):
            return record_id[len(table_prefix):]
        # Try common prefixes
        for prefix in ["videos:", "users:", "video:", "user:"]:
            if record_id.startswith(prefix):
                return record_id[len(prefix):]
        return record_id
    else:
        return str(record_id)


def format_record_id(record_id: Union[str, Dict], table_name: str) -> str:
    """
    Format a record ID for use in SurrealDB queries.

    Converts any ID format to the standard "table:id" format.

    Args:
        record_id: Record ID in any format
        table_name: Table name (without colon, e.g., "videos", "users")

    Returns:
        formatted_id: ID in "table:id" format (e.g., "videos:123")
    """
    if isinstance(record_id, dict):
        # Dict format: {"table_name": "video", "id": "123"}
        # Use the table name from the dict if available, otherwise use provided
        table = record_id.get("table_name", table_name)
        id_part = record_id.get("id", "")
        return f"{table}:{id_part}"
    elif isinstance(record_id, str):
        # String format: might be "video:123" or just "123"
        if ":" in record_id:
            # Already formatted
            return record_id
        else:
            # Just the ID part
            return f"{table_name}:{record_id}"
    else:
        return f"{table_name}:{str(record_id)}"


class EventType(Enum):
    """Types of video events to track."""

    # Positive engagement events
    VIEW = "view"
    WATCH = "watch"  # Significant watch time
    COMPLETE = "complete"  # Watched to end
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    FOLLOW_FROM_VIDEO = "follow_from_video"
    GIFT = "gift"
    SAVE = "save"
    REPLAY = "replay"  # User replayed the video

    # Negative signals
    SKIP = "skip"  # Quick scroll past
    DISMISS = "dismiss"  # User actively dismissed
    REPORT = "report"
    BLOCK_CREATOR = "block_creator"
    NOT_INTERESTED = "not_interested"

    # Virality signals (computed)
    TRENDING = "trending"
    VIRAL = "viral"
    FEATURED = "featured"


class VideoEventRecorder:
    """
    Records video interaction events to SurrealDB for model training.

    Event schema:
    {
        "id": "event:<uuid>",
        "type": "view|watch|like|skip|etc",
        "video_id": "video:<id>",
        "user_id": "user:<id>",
        "timestamp": datetime,
        "metadata": {
            "watch_time": seconds,
            "video_progress": 0.0-1.0,
            "source": "for_you|following|trending|search",
            "previous_videos": [list of recent video IDs],
            "session_id": session identifier
        }
    }
    """

    def __init__(self, db_client):
        """
        Initialize event recorder.

        Args:
            db_client: SurrealDB client instance
        """
        self.db = db_client

    async def record_view(
        self,
        video_id: str,
        user_id: str,
        source: str = "for_you",
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Record a video impression/view.

        Args:
            video_id: ID of the viewed video
            user_id: ID of the user
            source: Where the video was shown (for_you, following, trending, etc.)
            session_id: Optional session identifier

        Returns:
            event: Created event record
        """
        event = await self._create_event(
            event_type=EventType.VIEW,
            video_id=video_id,
            user_id=user_id,
            metadata={
                "source": source,
                "session_id": session_id
            }
        )

        # Increment view count on video
        formatted_video_id = format_record_id(video_id, "videos")
        await self.db.query(
            f"UPDATE {formatted_video_id} SET view_count += 1, updated_at = time::now()"
        )

        return event

    async def record_watch(
        self,
        video_id: str,
        user_id: str,
        watch_time: float,
        video_duration: float,
        source: str = "for_you",
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Record significant watch time on a video.

        Args:
            video_id: ID of the watched video
            user_id: ID of the user
            watch_time: Seconds watched
            video_duration: Total video duration in seconds
            source: Where the video was shown
            session_id: Optional session identifier

        Returns:
            event: Created event record
        """
        progress = min(1.0, watch_time / video_duration) if video_duration > 0 else 0.0

        event_type = EventType.COMPLETE if progress >= 0.95 else EventType.WATCH

        event = await self._create_event(
            event_type=event_type,
            video_id=video_id,
            user_id=user_id,
            metadata={
                "watch_time": watch_time,
                "video_duration": video_duration,
                "progress": progress,
                "source": source,
                "session_id": session_id
            }
        )

        # Update video metrics
        if progress >= 0.95:
            # Count as a completion
            formatted_video_id = format_record_id(video_id, "videos")
            await self.db.query(
                f"UPDATE {formatted_video_id} SET completion_count += 1, updated_at = time::now()"
            )

        return event

    async def record_engagement(
        self,
        event_type: EventType,
        video_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record engagement events (like, comment, share, etc.)

        Args:
            event_type: Type of engagement (LIKE, COMMENT, SHARE, etc.)
            video_id: ID of the video
            user_id: ID of the user
            metadata: Additional event metadata

        Returns:
            event: Created event record
        """
        event = await self._create_event(
            event_type=event_type,
            video_id=video_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        # Update corresponding counters
        formatted_video_id = format_record_id(video_id, "videos")
        if event_type == EventType.LIKE:
            await self.db.query(
                f"UPDATE {formatted_video_id} SET like_count += 1, updated_at = time::now()"
            )
        elif event_type == EventType.COMMENT:
            await self.db.query(
                f"UPDATE {formatted_video_id} SET comment_count += 1, updated_at = time::now()"
            )
        elif event_type == EventType.SHARE:
            await self.db.query(
                f"UPDATE {formatted_video_id} SET share_count += 1, updated_at = time::now()"
            )

        return event

    async def record_negative_signal(
        self,
        event_type: EventType,
        video_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record negative signals (skip, dismiss, not interested, etc.)

        These are crucial for learning what users DON'T want to see.

        Args:
            event_type: Type of negative signal (SKIP, DISMISS, etc.)
            video_id: ID of the video
            user_id: ID of the user
            metadata: Additional event metadata (e.g., skip_reason)

        Returns:
            event: Created event record
        """
        event = await self._create_event(
            event_type=event_type,
            video_id=video_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        logger.info(f"Recorded negative signal: {event_type.value} for video {video_id} by user {user_id}")

        return event

    async def record_skip(
        self,
        video_id: str,
        user_id: str,
        watch_time: float,
        video_duration: float,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Record when a user skips a video quickly.

        A skip is typically defined as watching < 3 seconds or < 10% of video.

        Args:
            video_id: ID of the skipped video
            user_id: ID of the user
            watch_time: Seconds watched before skip
            video_duration: Total video duration
            reason: Optional reason for skip

        Returns:
            event: Created event record
        """
        progress = min(1.0, watch_time / video_duration) if video_duration > 0 else 0.0

        return await self.record_negative_signal(
            event_type=EventType.SKIP,
            video_id=video_id,
            user_id=user_id,
            metadata={
                "watch_time": watch_time,
                "video_duration": video_duration,
                "progress": progress,
                "reason": reason
            }
        )

    async def _create_event(
        self,
        event_type: EventType,
        video_id: str,
        user_id: str,
        metadata: Dict
    ) -> Dict:
        """
        Create an event record in SurrealDB.

        Args:
            event_type: Type of event
            video_id: Video ID
            user_id: User ID
            metadata: Event metadata

        Returns:
            event: Created event record
        """
        query = """
            CREATE video_events CONTENT {
                type: $type,
                video_id: type::thing('videos', $video_id),
                user_id: type::thing('users', $user_id),
                timestamp: time::now(),
                metadata: $metadata
            }
        """

        result = await self.db.query(query, {
            "type": event_type.value,
            "video_id": normalize_id(video_id, "videos:"),
            "user_id": normalize_id(user_id, "users:"),
            "metadata": metadata
        })

        if result and len(result) > 0:
            return result[0]
        return {}

    async def get_user_events(
        self,
        user_id: str,
        limit: int = 100,
        event_types: Optional[List[EventType]] = None
    ) -> List[Dict]:
        """
        Get recent events for a user.

        Args:
            user_id: User ID
            limit: Maximum number of events to return
            event_types: Optional filter by event types

        Returns:
            events: List of event records
        """
        if event_types:
            types_filter = ", ".join([f"'{et.value}'" for et in event_types])
            query = f"""
                SELECT * FROM video_events
                WHERE user_id = type::thing('users', $user_id)
                AND type IN [{types_filter}]
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT * FROM video_events
                WHERE user_id = type::thing('users', $user_id)
                ORDER BY timestamp DESC
                LIMIT {limit}
            """

        result = await self.db.query(query, {
            "user_id": normalize_id(user_id, "users:")
        })

        return result if result else []

    async def get_video_events(
        self,
        video_id: str,
        limit: int = 1000,
        event_types: Optional[List[EventType]] = None
    ) -> List[Dict]:
        """
        Get events for a video.

        Args:
            video_id: Video ID
            limit: Maximum number of events to return
            event_types: Optional filter by event types

        Returns:
            events: List of event records
        """
        if event_types:
            types_filter = ", ".join([f"'{et.value}'" for et in event_types])
            query = f"""
                SELECT * FROM video_events
                WHERE video_id = type::thing('videos', $video_id)
                AND type IN [{types_filter}]
                ORDER BY timestamp DESC
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT * FROM video_events
                WHERE video_id = type::thing('videos', $video_id)
                ORDER BY timestamp DESC
                LIMIT {limit}
            """

        result = await self.db.query(query, {
            "video_id": normalize_id(video_id, "videos:")
        })

        return result if result else []

    async def compute_virality_metrics(self, video_id: str) -> Dict:
        """
        Compute virality metrics for a video based on recent events.

        Checks for:
        - Rapid view growth (viral)
        - High engagement rate (trending)
        - Sustained interest over time

        Args:
            video_id: Video ID

        Returns:
            metrics: Dict with virality signals
        """
        # Get events from last 24 hours
        query = """
            SELECT type, timestamp FROM video_events
            WHERE video_id = type::thing('videos', $video_id)
            AND timestamp > time::now() - 24h
            ORDER BY timestamp ASC
        """

        events = await self.db.query(query, {
            "video_id": normalize_id(video_id, "videos:")
        })

        if not events or len(events) < 10:
            return {
                "is_viral": False,
                "is_trending": False,
                "velocity": 0.0,
                "engagement_rate": 0.0
            }

        # Calculate metrics
        total_views = sum(1 for e in events if e['type'] == 'view')
        total_engagements = sum(
            1 for e in events
            if e['type'] in ['like', 'comment', 'share', 'complete']
        )

        engagement_rate = total_engagements / total_views if total_views > 0 else 0.0

        # Calculate velocity (views per hour)
        time_span_hours = 24.0  # Using 24 hour window
        velocity = total_views / time_span_hours

        # Thresholds for virality
        is_viral = velocity > 100 and engagement_rate > 0.1  # 100+ views/hour + 10% engagement
        is_trending = velocity > 50 or engagement_rate > 0.15

        return {
            "is_viral": is_viral,
            "is_trending": is_trending,
            "velocity": velocity,
            "engagement_rate": engagement_rate,
            "total_views_24h": total_views,
            "total_engagements_24h": total_engagements
        }


async def setup_event_schema(db_client):
    """
    Set up the video_events table schema in SurrealDB.

    Args:
        db_client: SurrealDB client instance
    """
    schema = """
        DEFINE TABLE video_events SCHEMAFULL;
        DEFINE FIELD type ON TABLE video_events TYPE string;
        DEFINE FIELD video_id ON TABLE video_events TYPE record<videos>;
        DEFINE FIELD user_id ON TABLE video_events TYPE record<users>;
        DEFINE FIELD timestamp ON TABLE video_events TYPE datetime;
        DEFINE FIELD metadata ON TABLE video_events TYPE object;

        DEFINE INDEX idx_video_events_video ON TABLE video_events COLUMNS video_id;
        DEFINE INDEX idx_video_events_user ON TABLE video_events COLUMNS user_id;
        DEFINE INDEX idx_video_events_timestamp ON TABLE video_events COLUMNS timestamp;
        DEFINE INDEX idx_video_events_type ON TABLE video_events COLUMNS type;

        -- Add completion_count field to videos table
        DEFINE FIELD completion_count ON TABLE videos TYPE int DEFAULT 0;
    """

    await db_client.query(schema)
    logger.info("Video events schema created successfully")
