"""Compatibility shim to provide `get_db()` used by older modules.

Provides an async `get_db()` that returns an AsyncSurreal client instance.
If an async client has already been attached to the global `db_client` it will be
returned, otherwise a new AsyncSurreal instance will be created and returned.
"""
from surrealdb import AsyncSurreal
from typing import Optional
from utils.config import settings
from db.surrealdb_client import db_client
import logging

logger = logging.getLogger(__name__)


async def get_db() -> AsyncSurreal:
    """Return an AsyncSurreal client connected to the configured DB.

    If an async client was attached to the project's global `db_client`, reuse it.
    Otherwise instantiate, connect, sign in and select namespace/database.
    """
    async_db: Optional[AsyncSurreal] = getattr(db_client, "async_db", None)
    if async_db is not None:
        return async_db

    # Create a temporary async client and connect
    logger.info("[db.client] Creating new AsyncSurreal client")
    async_db = AsyncSurreal(settings.SURREALDB_URL)
    await async_db.connect()
    try:
        if settings.ENVIRONMENT == "production":
            await async_db.signin({
                "username": settings.SURREALDB_USER,
                "password": settings.SURREALDB_PASS,
                "namespace": settings.SURREALDB_NS,
            })
        else:
            await async_db.signin({
                "username": settings.SURREALDB_USER,
                "password": settings.SURREALDB_PASS,
            })
    except Exception:
        # If signin fails, log and continue; some local setups do not require signin
        logger.info("[db.client] signin failed or not required")
    await async_db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
    # Do not attach to db_client here to avoid unexpected lifecycle changes
    return async_db
