"""
Embeddings API - Collision-less Embedding Management

Endpoints for:
- Adding/updating video embeddings
- Searching similar videos
- Embedding table management
- Performance metrics
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import numpy as np

from app.embeddings import (
    get_embedding_table,
    generate_dummy_embedding,
    compute_embedding_similarity,
    get_default_embedding,
    get_available_categories,
    should_create_dedicated_embedding,
    EMBEDDING_DIM,
    DEFAULT_CATEGORY_EMBEDDINGS,
    MIN_INTERACTIONS_FOR_EMBEDDING
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MODELS
# ============================================================================

class EmbeddingRequest(BaseModel):
    """Request to add/update video embedding."""
    video_id: str
    category: str
    embedding: Optional[List[float]] = None  # If None, generates dummy
    metadata: Optional[dict] = None


class EmbeddingSimilarityRequest(BaseModel):
    """Request to search similar videos."""
    video_id: Optional[str] = None  # Search by video ID
    embedding: Optional[List[float]] = None  # Or by embedding vector
    k: int = Field(default=10, ge=1, le=100)
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)
    category_filter: Optional[str] = None


class EmbeddingResponse(BaseModel):
    """Embedding operation response."""
    success: bool
    message: str
    video_id: Optional[str] = None
    embedding_dim: int = EMBEDDING_DIM


class SimilarityResult(BaseModel):
    """Similarity search result."""
    video_id: str
    similarity: float
    category: str
    metadata: dict


class SimilarityResponse(BaseModel):
    """Similarity search response."""
    query_video_id: Optional[str] = None
    results: List[SimilarityResult]
    total_results: int
    search_time_ms: float


# ============================================================================
# EMBEDDING MANAGEMENT
# ============================================================================

@router.post("/add", response_model=EmbeddingResponse)
async def add_embedding(request: EmbeddingRequest):
    """
    Add or update video embedding (collision-free).

    If embedding is not provided, generates a dummy embedding
    based on video_id and category (for testing).

    Args:
        request: Embedding request

    Returns:
        Success status
    """
    try:
        table = await get_embedding_table()

        # Generate or use provided embedding
        if request.embedding:
            embedding = np.array(request.embedding, dtype=np.float32)

            if embedding.shape[0] != EMBEDDING_DIM:
                raise HTTPException(
                    status_code=400,
                    detail=f"Embedding must be {EMBEDDING_DIM}-dimensional"
                )
        else:
            # Generate dummy embedding for testing
            embedding = await generate_dummy_embedding(
                request.video_id,
                request.category
            )

        # Add to table (collision-free)
        success = await table.add_embedding(
            video_id=request.video_id,
            embedding=embedding,
            category=request.category,
            metadata=request.metadata
        )

        if success:
            return EmbeddingResponse(
                success=True,
                message=f"Embedding added for {request.video_id}",
                video_id=request.video_id,
                embedding_dim=EMBEDDING_DIM
            )
        else:
            return EmbeddingResponse(
                success=False,
                message=f"Duplicate embedding detected for {request.video_id}",
                video_id=request.video_id,
                embedding_dim=EMBEDDING_DIM
            )

    except Exception as e:
        logger.error(f"Error adding embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=dict)
async def add_batch_embeddings(videos: List[EmbeddingRequest]):
    """
    Add multiple embeddings in batch (efficient).

    Args:
        videos: List of embedding requests

    Returns:
        Batch operation result
    """
    try:
        table = await get_embedding_table()

        # Prepare batch
        batch_data = []
        for req in videos:
            if req.embedding:
                embedding = np.array(req.embedding, dtype=np.float32)
            else:
                embedding = await generate_dummy_embedding(req.video_id, req.category)

            batch_data.append((req.video_id, embedding, req.category, req.metadata))

        # Add batch
        added_count = await table.add_batch(batch_data)

        return {
            "success": True,
            "total": len(videos),
            "added": added_count,
            "skipped": len(videos) - added_count,
            "message": f"Added {added_count}/{len(videos)} embeddings"
        }

    except Exception as e:
        logger.error(f"Error adding batch embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SIMILARITY SEARCH
# ============================================================================

@router.post("/search", response_model=SimilarityResponse)
async def search_similar_videos(request: EmbeddingSimilarityRequest):
    """
    Search for similar videos using embeddings (collision-free).

    Args:
        request: Similarity search request

    Returns:
        List of similar videos with scores
    """
    try:
        import time
        start_time = time.time()

        table = await get_embedding_table()

        # Get query embedding
        if request.video_id:
            # Search by video ID
            query_embedding = await table.get_embedding(request.video_id)
            if query_embedding is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Embedding not found for {request.video_id}"
                )
        elif request.embedding:
            # Search by embedding vector
            query_embedding = np.array(request.embedding, dtype=np.float32)

            if query_embedding.shape[0] != EMBEDDING_DIM:
                raise HTTPException(
                    status_code=400,
                    detail=f"Embedding must be {EMBEDDING_DIM}-dimensional"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either video_id or embedding"
            )

        # Search for similar videos
        results = await table.search_similar(
            query_embedding=query_embedding,
            k=request.k,
            min_similarity=request.min_similarity,
            category_filter=request.category_filter
        )

        search_time_ms = (time.time() - start_time) * 1000

        # Format results
        formatted_results = [
            SimilarityResult(
                video_id=r["video_id"],
                similarity=r["similarity"],
                category=r.get("category", "unknown"),
                metadata=r.get("metadata", {})
            )
            for r in results
        ]

        return SimilarityResponse(
            query_video_id=request.video_id,
            results=formatted_results,
            total_results=len(formatted_results),
            search_time_ms=round(search_time_ms, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching similar videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{video_id}")
async def get_similar_videos(
    video_id: str,
    k: int = Query(10, ge=1, le=100),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    category_filter: Optional[str] = Query(None)
):
    """
    Get similar videos for a given video ID (simple endpoint).

    Args:
        video_id: Video ID
        k: Number of results
        min_similarity: Minimum similarity threshold
        category_filter: Optional category filter

    Returns:
        Similar videos
    """
    request = EmbeddingSimilarityRequest(
        video_id=video_id,
        k=k,
        min_similarity=min_similarity,
        category_filter=category_filter
    )

    return await search_similar_videos(request)


# ============================================================================
# EMBEDDING TABLE MANAGEMENT
# ============================================================================

@router.get("/stats")
async def get_embedding_stats():
    """
    Get embedding table statistics.

    Returns:
        Table stats (total vectors, searches, cache hit rate, etc.)
    """
    try:
        table = await get_embedding_table()
        stats = table.get_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{video_id}")
async def get_video_embedding(video_id: str):
    """
    Get embedding vector for a video.

    Args:
        video_id: Video ID

    Returns:
        Embedding vector
    """
    try:
        table = await get_embedding_table()
        embedding = await table.get_embedding(video_id)

        if embedding is None:
            raise HTTPException(
                status_code=404,
                detail=f"Embedding not found for {video_id}"
            )

        return {
            "success": True,
            "video_id": video_id,
            "embedding": embedding.tolist(),
            "dimension": len(embedding)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove/{video_id}")
async def remove_video_embedding(video_id: str):
    """
    Remove embedding for a video.

    Args:
        video_id: Video ID

    Returns:
        Success status
    """
    try:
        table = await get_embedding_table()
        success = table.remove_embedding(video_id)

        if success:
            return {
                "success": True,
                "message": f"Embedding removed for {video_id}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Embedding not found for {video_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TESTING & UTILITIES
# ============================================================================

@router.post("/generate-dummy")
async def generate_dummy_embeddings(
    count: int = Query(100, ge=1, le=10000),
    categories: List[str] = Query(["sports", "comedy", "music", "gaming"])
):
    """
    Generate dummy embeddings for testing.

    Creates random embeddings with category patterns.

    Args:
        count: Number of embeddings to generate
        categories: Categories to use

    Returns:
        Generation result
    """
    try:
        table = await get_embedding_table()

        batch_data = []
        for i in range(count):
            video_id = f"video:{i+1}"
            category = categories[i % len(categories)]

            embedding = await generate_dummy_embedding(video_id, category)

            batch_data.append((
                video_id,
                embedding,
                category,
                {"generated": True, "index": i}
            ))

        added_count = await table.add_batch(batch_data)

        return {
            "success": True,
            "generated": count,
            "added": added_count,
            "categories": categories,
            "message": f"Generated {added_count} dummy embeddings"
        }

    except Exception as e:
        logger.error(f"Error generating dummy embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compute-similarity")
async def compute_pairwise_similarity(
    video_id1: str = Query(...),
    video_id2: str = Query(...)
):
    """
    Compute similarity between two videos.

    Args:
        video_id1: First video ID
        video_id2: Second video ID

    Returns:
        Cosine similarity score
    """
    try:
        table = await get_embedding_table()

        # Get embeddings
        emb1 = await table.get_embedding(video_id1)
        emb2 = await table.get_embedding(video_id2)

        if emb1 is None:
            raise HTTPException(
                status_code=404,
                detail=f"Embedding not found for {video_id1}"
            )

        if emb2 is None:
            raise HTTPException(
                status_code=404,
                detail=f"Embedding not found for {video_id2}"
            )

        # Compute similarity
        similarity = await compute_embedding_similarity(emb1, emb2)

        return {
            "success": True,
            "video_id1": video_id1,
            "video_id2": video_id2,
            "similarity": float(similarity),
            "similar": similarity >= 0.7
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing similarity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEFAULT CATEGORY EMBEDDINGS (Monolith-inspired)
# ============================================================================

@router.get("/categories")
async def get_categories():
    """
    Get list of available categories with default embeddings.

    Monolith-inspired: New/unpopular videos use category defaults.

    Returns:
        List of category names
    """
    try:
        categories = get_available_categories()

        return {
            "success": True,
            "categories": categories,
            "total": len(categories),
            "message": "These categories have pre-computed default embeddings"
        }

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default/{category}")
async def get_category_default_embedding(category: str):
    """
    Get default embedding for a category.

    Monolith-inspired: Used for new videos without dedicated embeddings.

    Args:
        category: Category name

    Returns:
        Default embedding for category
    """
    try:
        embedding = get_default_embedding(category)

        return {
            "success": True,
            "category": category,
            "embedding": embedding.tolist(),
            "dimension": len(embedding),
            "message": f"Default embedding for {category} category"
        }

    except Exception as e:
        logger.error(f"Error getting default embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/should-create/{video_id}")
async def check_should_create_embedding(
    video_id: str,
    interaction_count: Optional[int] = Query(None)
):
    """
    Check if video should have dedicated embedding.

    Monolith-inspired: Frequency filtering to save memory.
    Videos with < MIN_INTERACTIONS use category defaults.

    Args:
        video_id: Video ID
        interaction_count: Optional interaction count (views/likes)

    Returns:
        Whether to create dedicated embedding
    """
    try:
        should_create = await should_create_dedicated_embedding(
            video_id,
            interaction_count
        )

        return {
            "success": True,
            "video_id": video_id,
            "should_create_embedding": should_create,
            "min_interactions_threshold": MIN_INTERACTIONS_FOR_EMBEDDING,
            "interaction_count": interaction_count,
            "message": (
                f"Create dedicated embedding for {video_id}"
                if should_create
                else f"Use default category embedding for {video_id}"
            )
        }

    except Exception as e:
        logger.error(f"Error checking should create embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-expired")
async def cleanup_expired_embeddings():
    """
    Remove expired embeddings (not accessed within TTL).

    Monolith-inspired: Frees memory for inactive videos.
    Run this periodically (e.g., daily cron job).

    Returns:
        Number of embeddings removed
    """
    try:
        table = await get_embedding_table()
        removed_count = await table.cleanup_expired_embeddings()

        return {
            "success": True,
            "removed_count": removed_count,
            "ttl_days": table.ttl_days,
            "message": f"Cleaned up {removed_count} expired embeddings"
        }

    except Exception as e:
        logger.error(f"Error cleaning up expired embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
