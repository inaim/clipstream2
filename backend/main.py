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
from api import auth, social_auth, users, upload, feed
from starlette.responses import RedirectResponse

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
    logger.info("� Starting ClipStream Backend...")
    try:
        # Connect the existing blocking db_client (keeps current API compatible)
        await db_client.connect()
        logger.info("✅ Blocking SurrealDB client connected")

        # Additionally create an AsyncSurreal client and attach it to db_client
        # so parts of the app can use the async SDK directly if needed.
        try:
            async_db = AsyncSurreal(settings.SURREALDB_URL)
            await async_db.connect()
            # Signin with minimal payload (username/password/namespace)
            await async_db.signin({
                "username": settings.SURREALDB_USER,
                "password": settings.SURREALDB_PASS,
                "namespace": settings.SURREALDB_NS,
            })
            await async_db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
            # Attach to db_client for optional async access
            setattr(db_client, "async_db", async_db)
            logger.info("✅ Async SurrealDB client connected and attached to db_client")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize AsyncSurreal client: {e}")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

    yield

    # Shutdown
    logger.info("👋 Shutting down ClipStream Backend...")
    try:
        await db_client.disconnect()
        logger.info("✅ Database disconnected")
    except Exception as e:
        logger.error(f"❌ Database disconnection failed: {e}")
    # If an async Surreal client was attached to db_client, close it as well
    try:
        async_db = getattr(db_client, "async_db", None)
        if async_db is not None:
            await async_db.close()
            logger.info("✅ Async SurrealDB client closed")
    except Exception as e:
        logger.warning(f"⚠️  Failed to close async SurrealDB client: {e}")

# Create FastAPI app
app = FastAPI(
    title="ClipStream API",
    description="AI-Driven Video Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

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
    allow_origins=settings.ALLOWED_ORIGINS + [
        "https://clipstream.finailabz.com",
        "https://clipstream-backend.finailabz.com",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(social_auth.router, prefix="/api/v1/auth", tags=["Social Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(feed.router, prefix="/api/v1/feed", tags=["Feed"])


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