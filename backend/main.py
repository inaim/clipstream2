import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
# This allows imports to work whether running from backend/ or project root
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
# SessionMiddleware lives in Starlette; import from there to avoid version issues
from starlette.middleware.sessions import SessionMiddleware
# Respect X-Forwarded-* headers (scheme, host) when behind proxies / Cloud Run
try:
    from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
except Exception:
    ProxyHeadersMiddleware = None
    # We can't import ProxyHeadersMiddleware in this environment; at runtime
    # on the deployed service the package should be available. We'll emit a
    # warning at startup if it's missing so the operator knows to install
    # a compatible Starlette/uvicorn version.
from contextlib import asynccontextmanager
import logging

from utils.config import settings
from db.surrealdb_client import db_client
from surrealdb import AsyncSurreal
from api import auth, social_auth, users, upload, feed, videos, events
from api import notifications, messages, search, sounds, admin, analytics, interests
from api import graphql as graphql_api
from api import infinite_feed, realtime_events, embeddings_api, tiktok_ingestion
from app.tiktok_auto_ingestion import start_auto_ingestion, stop_auto_ingestion
from starlette.responses import RedirectResponse

# Import startup and ingestion modules
from app.startup import init_surreal, build_schema, verify_schema
from app.ingestion_engine import ingest_initial_videos, generate_demo_videos

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("CLIPSTREAM APP STARTUP LIFECYCLE")
    logger.info("=" * 60)

    try:
        # ============================================
        # STEP 1: Connect to SurrealDB
        # ============================================
        logger.info("\n[STEP 1] Connecting to SurrealDB...")

        # Connect the existing blocking db_client (keeps current API compatible)
        await db_client.connect()
        logger.info("Blocking SurrealDB client connected")

        # Additionally create an AsyncSurreal client and attach it to db_client
        # so parts of the app can use the async SDK directly if needed.
        try:
            async_db = AsyncSurreal(settings.SURREALDB_URL)
            await async_db.connect()

            # Different authentication for development vs production
            if settings.ENVIRONMENT == "production":
                # Production: Sign in with namespace-level credentials (SurrealDB Cloud)
                logger.info(f"[SURREALDB] Production mode: Using namespace-level auth for async client")
                await async_db.signin({
                    "username": settings.SURREALDB_USER,
                    "password": settings.SURREALDB_PASS,
                    "namespace": settings.SURREALDB_NS
                })
            else:
                # Development: Sign in with root-level credentials (local SurrealDB)
                logger.info(f"[SURREALDB] Development mode: Using root-level auth for async client")
                await async_db.signin({
                    "username": settings.SURREALDB_USER,
                    "password": settings.SURREALDB_PASS,
                })

            await async_db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
            # Attach to db_client for optional async access
            setattr(db_client, "async_db", async_db)
            logger.info("Async SurrealDB client connected and attached to db_client")
        except Exception as e:
            logger.warning(f"Failed to initialize AsyncSurreal client: {e}")

        # ============================================
        # STEP 2: Build Database Schema (Idempotent)
        # ============================================
        logger.info("\n[STEP 2] Building database schema...")
        try:
            await build_schema(async_db)
            logger.info("Schema built successfully")

            # Verify schema
            schema_info = await verify_schema(async_db)
            logger.info(f"Verified {len(schema_info)} tables")
        except Exception as e:
            logger.error(f"Schema building failed: {e}")

        # ============================================
        # STEP 3: Start Ingestion Engine
        # ============================================
        logger.info("\n[STEP 3] Starting video ingestion engine...")

        # Check if we should ingest demo videos (controlled by env var)
        ingest_demo = os.getenv("INGEST_DEMO_VIDEOS", "true").lower() == "true"

        if ingest_demo:
            try:
                # Generate demo videos for testing
                demo_count = int(os.getenv("DEMO_VIDEO_COUNT", "10"))
                logger.info(f"Generating {demo_count} demo videos...")
                demo_videos = await generate_demo_videos(count=demo_count)

                # Ingest demo videos
                result = await ingest_initial_videos(async_db, demo_videos)
                logger.info(
                    f"Ingestion complete: {result['ingested']}/{result['total']} videos ingested"
                )

                if result['errors']:
                    logger.warning(f"{len(result['errors'])} ingestion errors occurred")
            except Exception as e:
                logger.error(f"Demo video ingestion failed: {e}")
        else:
            logger.info("Demo video ingestion disabled (set INGEST_DEMO_VIDEOS=true to enable)")

        # ============================================
        # STEP 3.5: Start TikTok Auto-Ingestion
        # ============================================
        # Auto-start TikTok video scraping (enabled by default, disable with env flag)
        enable_tiktok = os.getenv("ENABLE_TIKTOK_AUTO_INGEST", "true").lower() in ("1", "true", "yes")

        if enable_tiktok:
            try:
                logger.info("\n[STEP 3.5] Starting TikTok auto-ingestion with browser scraping...")
                await start_auto_ingestion()
                logger.info("✅ TikTok auto-ingestion service started (browser scraping enabled)")
                logger.info("   - Scraping trending hashtags every 5 minutes")
                logger.info("   - Browser: Headless Chromium with infinite scroll")
                logger.info("   - Sources: #fyp, #viral, #trending, etc.")
            except Exception as e:
                logger.warning(f"⚠️  Failed to start TikTok auto-ingestion: {e}")
                logger.warning("   Make sure Playwright is installed: playwright install chromium")
        else:
            logger.info("\n[STEP 3.5] TikTok auto-ingestion disabled")
            logger.info("   Set ENABLE_TIKTOK_AUTO_INGEST=true to enable")

        # ============================================
        # STEP 4: Platform Ready
        # ============================================
        logger.info("\n[STEP 4] Platform ready for beta")
        logger.info("=" * 60)
        logger.info("ML-Powered Feed: /api/v1/feed/for-you?user_id=...")
        logger.info("Event Logging: POST /api/v1/events")
        logger.info("Video Upload: POST /api/upload")
        logger.info("Analytics: GET /api/v1/events/analytics/video/{id}")
        logger.info("Score Debug: GET /api/v1/feed/debug/explain-score")
        logger.info("=" * 60)
        logger.info("TikTok-Style ML Algorithm Active:")
        logger.info("  - User Interest (60%): Category prefs + embeddings")
        logger.info("  - Video Quality (30%): Engagement + age decay")
        logger.info("  - Exploration (10%): UCB discovery bonus")
        logger.info("=" * 60)
        logger.info("Clipstream backend ready - videos ingested, schema built, beta open")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Startup failed: {e}")

    yield

    # Shutdown
    logger.info("\n" + "=" * 60)
    logger.info("CLIPSTREAM APP SHUTDOWN")
    logger.info("=" * 60)
    logger.info("Shutting down ClipStream Backend...")
    try:
        await db_client.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error(f"Database disconnection failed: {e}")
    # If an async Surreal client was attached to db_client, close it as well
    try:
        async_db = getattr(db_client, "async_db", None)
        if async_db is not None:
            await async_db.close()
            logger.info("Async SurrealDB client closed")
    except Exception as e:
        logger.warning(f"Failed to close async SurrealDB client: {e}")

    # Stop TikTok auto-ingestion if it was started
    enable_tiktok = os.getenv("ENABLE_TIKTOK_AUTO_INGEST", "true").lower() in ("1", "true", "yes")
    if enable_tiktok:
        try:
            await stop_auto_ingestion()
            logger.info("TikTok auto-ingestion service stopped")
        except Exception as e:
            logger.warning(f"Failed to stop TikTok auto-ingestion: {e}")
    logger.info("=" * 60)

# Create FastAPI app
app = FastAPI(
    title="ClipStream API",
    description="AI-Driven Video Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Small, opt-in middleware for debugging incoming Authorization headers.
# Controlled by environment variable ENABLE_HEADER_DEBUG=1 to avoid leaking
# tokens or adding noise in production logs.
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware

class HeaderDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if os.getenv("ENABLE_HEADER_DEBUG", "0") == "1":
                auth = request.headers.get("authorization")
                if auth:
                    # only log masked length
                    try:
                        length = len(auth)
                    except Exception:
                        length = -1
                    logger.info(f"HeaderDebug: Authorization present (len={length})")
                else:
                    logger.info("HeaderDebug: Authorization header missing")
        except Exception as e:
            logger.warning(f"HeaderDebug middleware failure: {e}")
        return await call_next(request)

# Add the middleware early so other routers see it
app.add_middleware(HeaderDebugMiddleware)

# When running behind Cloud Run / a proxy, trust X-Forwarded-Proto so
# request.url_for(...) and other URL generation produce https scheme.
# Use a permissive trusted_hosts during deployment; tighten this if you
# want to restrict which proxy hosts are accepted.
if ProxyHeadersMiddleware is not None:
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
else:
    logger.warning("ProxyHeadersMiddleware not available; X-Forwarded headers may be ignored")

# Session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="clipstream_session",
    max_age=3600,
    same_site="lax",
    https_only=os.getenv("APP_ENV", "development") == "production"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=getattr(settings, 'CORS_ALLOW_CREDENTIALS', True),
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(social_auth.router, prefix="/api/v1/auth", tags=["Social Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(interests.router, prefix="/api/v1/users", tags=["Interests"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(videos.router, prefix="/api", tags=["Videos"])
app.include_router(feed.router, prefix="/api/v1/feed", tags=["Feed"])
app.include_router(events.router, prefix="/api/v1", tags=["Events"])
app.include_router(infinite_feed.router, prefix="/api/v1/infinite", tags=["Infinite Feed"])
app.include_router(realtime_events.router, prefix="/api/v1/realtime", tags=["Real-time Events"])
app.include_router(embeddings_api.router, prefix="/api/v1/embeddings", tags=["Embeddings"])
app.include_router(tiktok_ingestion.router, prefix="/api/v1/tiktok-ingestion", tags=["TikTok Auto-Ingestion"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])
app.include_router(search.router, prefix="/api/v1", tags=["Search & Discover"])
app.include_router(sounds.router, prefix="/api/v1/sounds", tags=["Sounds"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

# Mount GraphQL endpoint at /graphql for querying videos and feed
app.mount("/graphql", graphql_api.graphql_app)

# Global exception handler for debugging
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.method} {request.url.path}: {exc}")
    return {"detail": str(exc)}


# Compatibility aliases: support legacy endpoints under /api/v1/social/* by
# redirecting them to the mounted /api/v1/auth/social/* routes. These keep
# the original query string so OAuth code/state are preserved.
@app.get("/api/v1/social/{provider}")
async def social_alias(request: Request, provider: str):
    qs = request.scope.get("query_string", b"").decode()
    target = f"/api/v1/auth/social/{provider}"
    if qs:
        target = f"{target}?{qs}"
    return RedirectResponse(target)


@app.get("/api/v1/social/{provider}/callback")
async def social_callback_alias(request: Request, provider: str):
    qs = request.scope.get("query_string", b"").decode()
    target = f"/api/v1/auth/social/{provider}/callback"
    if qs:
        target = f"{target}?{qs}"
    return RedirectResponse(target)


@app.get("/api/v1/social/callback")
async def social_callback_query_alias(request: Request):
    qs = request.scope.get("query_string", b"").decode()
    target = "/api/v1/auth/social/callback"
    if qs:
        target = f"{target}?{qs}"
    return RedirectResponse(target)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "ClipStream API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Check database connection
        db_status = "connected" if db_client._connected else "disconnected"

        return {
            "status": "healthy",
            "database": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )
