from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import logging
from db.surrealdb_client import db_client
from api import auth, feed, social_auth
from utils.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting ClipStream API...")
    await db_client.connect()
    yield
    logger.info("👋 Shutting down...")
    await db_client.disconnect()

app = FastAPI(
    title="ClipStream API",
    version="1.0.0",
    lifespan=lifespan
)

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_TO_A_RANDOM_SECRET_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(feed.router, prefix="/api/v1/feed", tags=["Feed"])
app.include_router(social_auth.router, prefix="/api/v1/auth", tags=["SocialAuth"])

@app.get("/")
async def root():
    return {"name": "ClipStream API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
