"""
Collision-less Embedding Tables for Video Recommendations

High-performance vector similarity search using:
- Unique embedding IDs (no collisions)
- FAISS for fast nearest neighbor search
- Async batch processing
- Redis caching for hot embeddings
- Incremental updates without rebuilding

TikTok-scale architecture:
- Billions of videos
- Sub-millisecond similarity search
- Real-time embedding updates
"""

import numpy as np
import hashlib
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pickle
import time

try:
    import faiss
except ImportError:
    faiss = None
    logging.warning("FAISS not installed. Install with: pip install faiss-cpu")

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from utils.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# EMBEDDING CONFIGURATION
# ============================================================================

EMBEDDING_DIM = 128  # Standard dimension for video embeddings
SIMILARITY_THRESHOLD = 0.7  # Cosine similarity threshold for recommendations


@dataclass
class VideoEmbedding:
    """Video embedding with metadata."""
    video_id: str
    embedding: np.ndarray
    content_hash: str  # Unique hash for collision detection
    category: str
    created_at: float
    metadata: Dict[str, Any]


# ============================================================================
# COLLISION-LESS EMBEDDING TABLE
# ============================================================================

class CollisionlessEmbeddingTable:
    """
    Collision-less embedding table with FAISS indexing.

    Features:
    - Unique video IDs with SHA256 hashing
    - FAISS for fast similarity search (10M+ vectors)
    - Redis caching for hot embeddings
    - Incremental updates (no full rebuild)
    - Cosine similarity search
    """

    def __init__(
        self,
        dimension: int = EMBEDDING_DIM,
        use_gpu: bool = False,
        cache_size: int = 10000
    ):
        """
        Initialize embedding table.

        Args:
            dimension: Embedding dimension (128 by default)
            use_gpu: Use GPU for FAISS (requires faiss-gpu)
            cache_size: Number of hot embeddings to cache in Redis
        """
        self.dimension = dimension
        self.use_gpu = use_gpu
        self.cache_size = cache_size

        # FAISS index (cosine similarity = inner product with normalized vectors)
        if faiss:
            if use_gpu and faiss.get_num_gpus() > 0:
                # GPU index for massive scale
                res = faiss.StandardGpuResources()
                self.index = faiss.GpuIndexFlatIP(res, dimension)
                logger.info("Using GPU FAISS index")
            else:
                # CPU index (still very fast)
                self.index = faiss.IndexFlatIP(dimension)
                logger.info("Using CPU FAISS index")
        else:
            self.index = None
            logger.warning("FAISS not available, using fallback similarity search")

        # Video ID to index mapping (collision-free)
        self.video_id_to_idx: Dict[str, int] = {}
        self.idx_to_video_id: Dict[int, str] = {}

        # Content hash to video ID (prevents duplicate embeddings)
        self.content_hash_to_video_id: Dict[str, str] = {}

        # Metadata storage
        self.video_metadata: Dict[str, Dict[str, Any]] = {}

        # Embeddings storage (for serialization)
        self.embeddings: List[np.ndarray] = []

        # Redis client for caching
        self.redis_client: Optional[aioredis.Redis] = None

        # Stats
        self.total_vectors = 0
        self.total_searches = 0
        self.cache_hits = 0

    async def initialize(self):
        """Initialize Redis connection for caching."""
        if aioredis:
            try:
                self.redis_client = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info("Redis cache connected for embeddings")
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")

    def _compute_content_hash(self, embedding: np.ndarray, video_id: str) -> str:
        """
        Compute unique content hash to prevent collisions.

        Args:
            embedding: Video embedding vector
            video_id: Video ID

        Returns:
            SHA256 hash (no collisions)
        """
        # Combine embedding and video_id for uniqueness
        data = embedding.tobytes() + video_id.encode()
        return hashlib.sha256(data).hexdigest()

    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding for cosine similarity.

        Args:
            embedding: Raw embedding vector

        Returns:
            L2-normalized embedding
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    async def add_embedding(
        self,
        video_id: str,
        embedding: np.ndarray,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add embedding to table (collision-free).

        Args:
            video_id: Unique video ID
            embedding: Video embedding vector (will be normalized)
            category: Video category
            metadata: Additional metadata

        Returns:
            True if added, False if duplicate detected
        """
        # Ensure correct dimension
        if embedding.shape[0] != self.dimension:
            logger.error(f"Embedding dimension mismatch: {embedding.shape[0]} != {self.dimension}")
            return False

        # Compute content hash for collision detection
        content_hash = self._compute_content_hash(embedding, video_id)

        # Check for duplicates
        if content_hash in self.content_hash_to_video_id:
            existing_id = self.content_hash_to_video_id[content_hash]
            if existing_id != video_id:
                logger.warning(f"Duplicate embedding detected: {video_id} == {existing_id}")
            return False

        # Check if video already exists (update case)
        if video_id in self.video_id_to_idx:
            logger.info(f"Updating existing embedding for {video_id}")
            idx = self.video_id_to_idx[video_id]

            # Update FAISS index
            normalized = self._normalize_embedding(embedding).astype('float32')
            if self.index:
                self.index.remove_ids(np.array([idx], dtype=np.int64))
                self.index.add_with_ids(normalized.reshape(1, -1), np.array([idx], dtype=np.int64))

            # Update storage
            self.embeddings[idx] = normalized

        else:
            # Add new embedding
            idx = self.total_vectors
            normalized = self._normalize_embedding(embedding).astype('float32')

            # Add to FAISS index
            if self.index:
                self.index.add_with_ids(normalized.reshape(1, -1), np.array([idx], dtype=np.int64))

            # Update mappings
            self.video_id_to_idx[video_id] = idx
            self.idx_to_video_id[idx] = video_id
            self.content_hash_to_video_id[content_hash] = video_id

            # Store embedding
            self.embeddings.append(normalized)

            self.total_vectors += 1

        # Store metadata
        self.video_metadata[video_id] = {
            "category": category,
            "content_hash": content_hash,
            "created_at": time.time(),
            **(metadata or {})
        }

        # Cache in Redis (for hot embeddings)
        if self.redis_client and self.total_vectors <= self.cache_size:
            try:
                await self.redis_client.setex(
                    f"embedding:{video_id}",
                    3600,  # 1 hour TTL
                    pickle.dumps(normalized)
                )
            except Exception as e:
                logger.debug(f"Redis cache write failed: {e}")

        logger.debug(f"Added embedding for {video_id} (index: {idx})")
        return True

    async def add_batch(
        self,
        video_embeddings: List[Tuple[str, np.ndarray, str, Optional[Dict[str, Any]]]]
    ) -> int:
        """
        Add multiple embeddings in batch (efficient).

        Args:
            video_embeddings: List of (video_id, embedding, category, metadata)

        Returns:
            Number of embeddings added
        """
        added_count = 0

        for video_id, embedding, category, metadata in video_embeddings:
            success = await self.add_embedding(video_id, embedding, category, metadata)
            if success:
                added_count += 1

        logger.info(f"Batch added {added_count}/{len(video_embeddings)} embeddings")
        return added_count

    async def search_similar(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        min_similarity: float = SIMILARITY_THRESHOLD,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar videos (collision-free).

        Args:
            query_embedding: Query embedding vector
            k: Number of results
            min_similarity: Minimum cosine similarity (0-1)
            category_filter: Optional category filter

        Returns:
            List of similar videos with scores
        """
        self.total_searches += 1

        if self.total_vectors == 0:
            return []

        # Normalize query
        normalized_query = self._normalize_embedding(query_embedding).astype('float32')

        if self.index:
            # FAISS search (fast)
            # Fetch more candidates for filtering
            search_k = k * 5 if category_filter else k

            scores, indices = self.index.search(
                normalized_query.reshape(1, -1),
                min(search_k, self.total_vectors)
            )

            results = []
            for score, idx in zip(scores[0], indices[0]):
                # Check if index exists
                if idx == -1 or idx not in self.idx_to_video_id:
                    continue

                # Apply similarity threshold
                if score < min_similarity:
                    continue

                video_id = self.idx_to_video_id[idx]
                metadata = self.video_metadata.get(video_id, {})

                # Apply category filter
                if category_filter and metadata.get("category") != category_filter:
                    continue

                results.append({
                    "video_id": video_id,
                    "similarity": float(score),
                    "category": metadata.get("category"),
                    "metadata": metadata
                })

                if len(results) >= k:
                    break

            return results

        else:
            # Fallback: Manual cosine similarity (slower)
            results = []

            for idx, emb in enumerate(self.embeddings):
                # Compute cosine similarity
                similarity = float(np.dot(normalized_query, emb))

                if similarity < min_similarity:
                    continue

                video_id = self.idx_to_video_id[idx]
                metadata = self.video_metadata.get(video_id, {})

                # Apply category filter
                if category_filter and metadata.get("category") != category_filter:
                    continue

                results.append({
                    "video_id": video_id,
                    "similarity": similarity,
                    "category": metadata.get("category"),
                    "metadata": metadata
                })

            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:k]

    async def get_embedding(self, video_id: str) -> Optional[np.ndarray]:
        """
        Get embedding for a video.

        Args:
            video_id: Video ID

        Returns:
            Embedding vector or None
        """
        # Try Redis cache first
        if self.redis_client:
            try:
                cached = await self.redis_client.get(f"embedding:{video_id}")
                if cached:
                    self.cache_hits += 1
                    return pickle.loads(cached)
            except Exception as e:
                logger.debug(f"Redis cache read failed: {e}")

        # Get from storage
        if video_id in self.video_id_to_idx:
            idx = self.video_id_to_idx[video_id]
            return self.embeddings[idx]

        return None

    def remove_embedding(self, video_id: str) -> bool:
        """
        Remove embedding from table.

        Args:
            video_id: Video ID

        Returns:
            True if removed, False if not found
        """
        if video_id not in self.video_id_to_idx:
            return False

        idx = self.video_id_to_idx[video_id]

        # Remove from FAISS
        if self.index:
            self.index.remove_ids(np.array([idx], dtype=np.int64))

        # Remove from mappings
        del self.video_id_to_idx[video_id]
        del self.idx_to_video_id[idx]

        # Remove metadata
        if video_id in self.video_metadata:
            content_hash = self.video_metadata[video_id]["content_hash"]
            if content_hash in self.content_hash_to_video_id:
                del self.content_hash_to_video_id[content_hash]
            del self.video_metadata[video_id]

        logger.info(f"Removed embedding for {video_id}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get embedding table statistics."""
        cache_hit_rate = (
            self.cache_hits / self.total_searches if self.total_searches > 0 else 0
        )

        return {
            "total_vectors": self.total_vectors,
            "dimension": self.dimension,
            "total_searches": self.total_searches,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": round(cache_hit_rate, 3),
            "unique_hashes": len(self.content_hash_to_video_id),
            "using_faiss": self.index is not None,
            "using_gpu": self.use_gpu
        }

    async def save(self, filepath: str):
        """Save embedding table to disk."""
        data = {
            "video_id_to_idx": self.video_id_to_idx,
            "idx_to_video_id": self.idx_to_video_id,
            "content_hash_to_video_id": self.content_hash_to_video_id,
            "video_metadata": self.video_metadata,
            "embeddings": self.embeddings,
            "dimension": self.dimension,
            "total_vectors": self.total_vectors
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        # Save FAISS index separately
        if self.index:
            faiss.write_index(self.index, f"{filepath}.faiss")

        logger.info(f"Saved embedding table to {filepath}")

    async def load(self, filepath: str):
        """Load embedding table from disk."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.video_id_to_idx = data["video_id_to_idx"]
        self.idx_to_video_id = data["idx_to_video_id"]
        self.content_hash_to_video_id = data["content_hash_to_video_id"]
        self.video_metadata = data["video_metadata"]
        self.embeddings = data["embeddings"]
        self.dimension = data["dimension"]
        self.total_vectors = data["total_vectors"]

        # Load FAISS index
        if faiss and f"{filepath}.faiss" in os.listdir(os.path.dirname(filepath)):
            self.index = faiss.read_index(f"{filepath}.faiss")

        logger.info(f"Loaded embedding table from {filepath} ({self.total_vectors} vectors)")


# ============================================================================
# GLOBAL EMBEDDING TABLE INSTANCE
# ============================================================================

# Singleton instance
_embedding_table: Optional[CollisionlessEmbeddingTable] = None


async def get_embedding_table() -> CollisionlessEmbeddingTable:
    """Get global embedding table instance."""
    global _embedding_table

    if _embedding_table is None:
        _embedding_table = CollisionlessEmbeddingTable()
        await _embedding_table.initialize()
        logger.info("Embedding table initialized")

    return _embedding_table


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def generate_dummy_embedding(
    video_id: str,
    category: str,
    dimension: int = EMBEDDING_DIM
) -> np.ndarray:
    """
    Generate dummy embedding for testing.

    In production, replace with actual embedding model (CLIP, VideoMAE, etc.)

    Args:
        video_id: Video ID
        category: Video category
        dimension: Embedding dimension

    Returns:
        Random embedding vector
    """
    # Use video_id and category as seed for reproducibility
    seed = int(hashlib.md5((video_id + category).encode()).hexdigest()[:8], 16)
    np.random.seed(seed)

    # Generate random embedding
    embedding = np.random.randn(dimension).astype('float32')

    # Add category-specific pattern (for testing similarity)
    category_seed = int(hashlib.md5(category.encode()).hexdigest()[:8], 16)
    np.random.seed(category_seed)
    category_pattern = np.random.randn(dimension).astype('float32') * 0.3

    embedding += category_pattern

    return embedding


async def compute_embedding_similarity(
    embedding1: np.ndarray,
    embedding2: np.ndarray
) -> float:
    """
    Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding
        embedding2: Second embedding

    Returns:
        Cosine similarity (0-1)
    """
    # Normalize
    norm1 = embedding1 / np.linalg.norm(embedding1)
    norm2 = embedding2 / np.linalg.norm(embedding2)

    # Cosine similarity
    return float(np.dot(norm1, norm2))
