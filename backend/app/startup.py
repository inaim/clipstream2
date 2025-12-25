"""
SurrealDB Schema Builder and Initialization

This module runs at application startup to ensure all required database
tables, indexes, and relations are properly defined.
"""

import logging
from surrealdb import AsyncSurreal

logger = logging.getLogger(__name__)


async def init_surreal(db_url: str, user: str, password: str, namespace: str, database: str):
    """
    Initialize SurrealDB connection and build schema.

    This is idempotent - running it multiple times is safe.

    Args:
        db_url: WebSocket URL for SurrealDB (e.g., ws://localhost:8000/rpc)
        user: Database user (root for dev, namespace user for prod)
        password: Database password
        namespace: SurrealDB namespace
        database: SurrealDB database name

    Returns:
        AsyncSurreal: Connected database instance
    """
    logger.info(f"Initializing SurrealDB at {db_url}")

    db = AsyncSurreal(db_url)
    await db.connect()

    # Authenticate
    await db.signin({"user": user, "pass": password})

    # Select namespace and database
    await db.use(namespace, database)
    logger.info(f"Using namespace '{namespace}' and database '{database}'")

    # Build schema (idempotent - can run multiple times safely)
    await build_schema(db)

    return db


async def build_schema(db: AsyncSurreal):
    """
    Define all tables, indexes, and relations for Clipstream.

    This schema supports:
    - Video ingestion and metadata
    - User profiles and authentication
    - Event tracking for ML training
    - Model metadata and versioning
    - Social features (likes, follows, comments)
    """

    schema = """
    -- ============================================
    -- CORE TABLES
    -- ============================================

    -- Videos table: stores all video content and metadata
    DEFINE TABLE video SCHEMALESS;
    DEFINE INDEX video_category_idx ON TABLE video COLUMNS category;
    DEFINE INDEX video_last_seen_idx ON TABLE video COLUMNS last_seen_ts;
    DEFINE INDEX video_created_idx ON TABLE video COLUMNS created_at;
    DEFINE INDEX video_status_idx ON TABLE video COLUMNS status;

    -- Users table: user profiles and authentication
    DEFINE TABLE user SCHEMALESS;
    DEFINE INDEX user_email_idx ON TABLE user COLUMNS email UNIQUE;
    DEFINE INDEX user_created_idx ON TABLE user COLUMNS created_at;

    -- Events table: user interaction tracking for ML training
    DEFINE TABLE event SCHEMALESS;
    DEFINE INDEX event_timestamp_idx ON TABLE event COLUMNS timestamp;
    DEFINE INDEX event_user_idx ON TABLE event COLUMNS user_id;
    DEFINE INDEX event_video_idx ON TABLE event COLUMNS video_id;
    DEFINE INDEX event_type_idx ON TABLE event COLUMNS event_type;

    -- Model table: ML model metadata and versioning
    DEFINE TABLE model SCHEMALESS;
    DEFINE INDEX model_version_idx ON TABLE model COLUMNS version;
    DEFINE INDEX model_created_idx ON TABLE model COLUMNS created_at;

    -- ============================================
    -- SOCIAL FEATURES (Graph Relations)
    -- ============================================

    -- Likes: user -> video interactions
    DEFINE TABLE likes SCHEMALESS;
    DEFINE INDEX likes_user_idx ON TABLE likes COLUMNS in;
    DEFINE INDEX likes_video_idx ON TABLE likes COLUMNS out;

    -- Follows: user -> user relationships
    DEFINE TABLE follows SCHEMALESS;
    DEFINE INDEX follows_follower_idx ON TABLE follows COLUMNS in;
    DEFINE INDEX follows_following_idx ON TABLE follows COLUMNS out;

    -- Comments: user comments on videos
    DEFINE TABLE comment SCHEMALESS;
    DEFINE INDEX comment_video_idx ON TABLE comment COLUMNS video_id;
    DEFINE INDEX comment_user_idx ON TABLE comment COLUMNS user_id;
    DEFINE INDEX comment_created_idx ON TABLE comment COLUMNS created_at;

    -- ============================================
    -- ANALYTICS & MONETIZATION
    -- ============================================

    -- Earnings: token rewards for creators
    DEFINE TABLE earnings SCHEMALESS;
    DEFINE INDEX earnings_user_idx ON TABLE earnings COLUMNS user_id;
    DEFINE INDEX earnings_video_idx ON TABLE earnings COLUMNS video_id;
    DEFINE INDEX earnings_created_idx ON TABLE earnings COLUMNS created_at;

    -- ============================================
    -- CONTENT MODERATION
    -- ============================================

    -- Reports: user-reported content
    DEFINE TABLE report SCHEMALESS;
    DEFINE INDEX report_video_idx ON TABLE report COLUMNS video_id;
    DEFINE INDEX report_status_idx ON TABLE report COLUMNS status;
    """

    try:
        await db.query(schema)
        logger.info("✅ SurrealDB schema built successfully")
    except Exception as e:
        logger.error(f"❌ Failed to build schema: {e}")
        raise


async def verify_schema(db: AsyncSurreal) -> dict:
    """
    Verify that all required tables exist and return schema info.

    Returns:
        dict: Schema verification results with table counts
    """
    tables = ["video", "user", "event", "model", "likes", "follows", "comment", "earnings", "report"]
    results = {}

    for table in tables:
        try:
            query_result = await db.query(f"SELECT count() FROM {table} GROUP ALL")
            count = 0
            if query_result and len(query_result) > 0 and query_result[0].get('result'):
                count = query_result[0]['result'][0].get('count', 0) if query_result[0]['result'] else 0

            results[table] = {
                "exists": True,
                "count": count
            }
            logger.info(f"✓ Table '{table}' exists with {count} records")
        except Exception as e:
            results[table] = {
                "exists": False,
                "error": str(e)
            }
            logger.warning(f"✗ Table '{table}' verification failed: {e}")

    return results
