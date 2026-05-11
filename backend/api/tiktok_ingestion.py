"""
TikTok Auto-Ingestion API

Endpoints to control the automatic TikTok video ingestion service.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.tiktok_auto_ingestion import (
    get_auto_ingestion_service,
    start_auto_ingestion,
    stop_auto_ingestion,
    get_ingestion_stats
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MODELS
# ============================================================================

class IngestionConfig(BaseModel):
    """Configuration for auto-ingestion service."""
    fetch_interval: int = Field(default=300, ge=60, le=3600, description="Seconds between fetches")
    videos_per_fetch: int = Field(default=10, ge=1, le=50, description="Videos per fetch")
    use_browser: bool = Field(default=True, description="Use browser scraping for feed discovery")
    use_stealth_mode: bool = Field(default=True, description="Enable advanced stealth scraper")
    proxy: str = Field(default=None, description="Proxy server URL (e.g., 'http://proxy:port')")
    target_user: str | None = Field(default=None, description="TikTok username to scrape (without @)")


class IngestionStatus(BaseModel):
    """Auto-ingestion service status."""
    is_running: bool
    fetch_interval: int
    videos_per_fetch: int
    use_browser: bool
    use_stealth_mode: bool = True
    proxy: str = None
    target_user: str | None = None
    total_fetched: int
    total_ingested: int
    total_failed: int
    success_rate: float
    last_fetch_time: float = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/start")
async def start_ingestion_service(config: IngestionConfig = None):
    """
    Start the TikTok auto-ingestion service.

    This will:
    - Fetch trending TikTok videos every N seconds
    - Download them automatically
    - Ingest into the platform
    - Make them available in the feed

    Args:
        config: Optional configuration (fetch_interval, videos_per_fetch)

    Returns:
        Service status
    """
    try:
        service = await get_auto_ingestion_service()

        # Update configuration if provided
        if config:
            service.fetch_interval = config.fetch_interval
            service.videos_per_fetch = config.videos_per_fetch
            service.use_browser = config.use_browser
            if config.proxy:
                service.proxy = config.proxy
            service.use_stealth_mode = config.use_stealth_mode
            service.target_user = config.target_user

        await service.start()

        return {
            "success": True,
            "message": "TikTok auto-ingestion started",
            "status": service.get_stats()
        }

    except Exception as e:
        logger.error(f"Error starting auto-ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_ingestion_service():
    """
    Stop the TikTok auto-ingestion service.

    Returns:
        Service status
    """
    try:
        service = await get_auto_ingestion_service()
        await service.stop()

        return {
            "success": True,
            "message": "TikTok auto-ingestion stopped",
            "status": service.get_stats()
        }

    except Exception as e:
        logger.error(f"Error stopping auto-ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_ingestion_status():
    """
    Get current status of auto-ingestion service.

    Returns:
        Service statistics
    """
    try:
        stats = await get_ingestion_stats()

        return {
            "success": True,
            "status": stats
        }

    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-now")
async def trigger_ingestion_now():
    """
    Manually trigger an ingestion cycle immediately.

    Useful for testing or forcing an update.

    Returns:
        Ingestion result
    """
    try:
        service = await get_auto_ingestion_service()

        # Trigger one ingestion cycle
        await service._fetch_and_ingest()

        return {
            "success": True,
            "message": "Ingestion triggered",
            "status": service.get_stats()
        }

    except Exception as e:
        logger.error(f"Error triggering ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
