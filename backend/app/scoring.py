"""
Video Scoring & Recommendation Engine

TikTok-style monolithic recommendation algorithm with:
- User interest modeling based on category and embedding similarity
- Video quality scoring with engagement metrics
- Exploration bonus (UCB-style) for discovery
- Age decay for freshness
- Dead video filtering

This is the core ranking algorithm that powers the "For You" feed.
"""

import math
import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION CONSTANTS
# ============================================

# Video is considered "dead" if not shown in X days
VIDEO_DEAD_THRESHOLD = 14 * 24 * 3600  # 14 days in seconds

# Smoothing factor for low-impression videos (Laplace smoothing)
VIDEO_IMPRESSIONS_SMOOTHING = 50

# Exploration coefficient (UCB-style)
EXPLORATION_COEFF = 0.5

# Engagement weight coefficients
ENGAGEMENT_WEIGHTS = {
    "watch_ratio": 0.4,       # Average watch percentage
    "completion_rate": 0.3,   # % of users who watched to end
    "like_rate": 0.2,         # % of users who liked
    "rewatch_rate": 0.1,      # % of users who rewatched
    "skip_penalty": -0.3,     # Penalty for early skips
}

# User interest weight coefficients
USER_INTEREST_WEIGHTS = {
    "category_watch": 0.4,    # User's avg watch time in this category
    "category_like": 0.3,     # User's like rate in this category
    "embedding_sim": 0.3,     # Cosine similarity between user & video embeddings
}

# Final score weight coefficients
FINAL_SCORE_WEIGHTS = {
    "user_interest": 0.6,     # Personalization
    "video_quality": 0.3,     # Global video quality
    "exploration": 0.1,       # Discovery bonus
}

# Age decay parameters
AGE_DECAY_HALFLIFE = 30 * 24 * 3600  # 30 days in seconds


# ============================================
# UTILITY FUNCTIONS
# ============================================

def cosine_similarity(a: Optional[List[float]], b: Optional[List[float]]) -> float:
    """
    Compute cosine similarity between two embedding vectors.

    Args:
        a: First embedding vector
        b: Second embedding vector

    Returns:
        float: Cosine similarity in range [-1, 1], or 0.0 if either is None
    """
    if a is None or b is None or len(a) == 0 or len(b) == 0:
        return 0.0

    try:
        a_arr = np.array(a, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)

        denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        if denom == 0:
            return 0.0

        return float(np.dot(a_arr, b_arr) / denom)
    except Exception as e:
        logger.warning(f"Error computing cosine similarity: {e}")
        return 0.0


# ============================================
# VIDEO QUALITY SCORING
# ============================================

def compute_video_score(video: Dict[str, Any], now: float) -> float:
    """
    Compute the global quality score for a video based on engagement metrics.

    This measures how well a video performs on average across all users.

    Metrics considered:
    - Average watch ratio (how much users watch)
    - Completion rate (% who watched to end)
    - Like rate (% who liked)
    - Rewatch rate (% who rewatched)
    - Skip rate (% who skipped early - penalty)

    The score is smoothed for low-impression videos and decayed by age.

    Args:
        video: Video document with stats
        now: Current timestamp (seconds since epoch)

    Returns:
        float: Video quality score (0.0 - 1.0 range typically)
    """
    stats = video.get("stats", {})
    N = stats.get("impressions", 0)

    # No data yet - return neutral score
    if N == 0:
        return 0.0

    # Calculate engagement rates
    avg_watch = stats.get("total_watch_ratio", 0) / N
    completion_rate = stats.get("completions", 0) / N
    like_rate = stats.get("likes", 0) / N
    skip_rate = stats.get("early_skips", 0) / N
    rewatch_rate = stats.get("rewatches", 0) / N

    # Weighted sum of engagement metrics
    raw_score = (
        ENGAGEMENT_WEIGHTS["watch_ratio"] * avg_watch +
        ENGAGEMENT_WEIGHTS["completion_rate"] * completion_rate +
        ENGAGEMENT_WEIGHTS["like_rate"] * like_rate +
        ENGAGEMENT_WEIGHTS["rewatch_rate"] * rewatch_rate +
        ENGAGEMENT_WEIGHTS["skip_penalty"] * skip_rate
    )

    # Laplace smoothing: trust videos with more impressions
    # Videos with < SMOOTHING impressions get discounted
    smoothed_score = (N / (N + VIDEO_IMPRESSIONS_SMOOTHING)) * raw_score

    # Age decay: newer videos get boosted
    # Half-life of AGE_DECAY_HALFLIFE (default 30 days)
    age = now - video.get("created_at", now)
    age_decay = 0.5 ** (age / AGE_DECAY_HALFLIFE)

    return smoothed_score * age_decay


# ============================================
# USER INTEREST MODELING
# ============================================

def compute_user_interest(user: Dict[str, Any], video: Dict[str, Any]) -> float:
    """
    Compute how interested this specific user is in this specific video.

    This is the personalization component that makes each user's feed unique.

    Factors:
    1. Category interest: Does the user like this category?
    2. Embedding similarity: How similar is video to user's past preferences?

    Args:
        user: User document with category stats and embedding
        video: Video document with category and embedding

    Returns:
        float: User interest score (0.0 - 1.0 range typically)
    """
    category = video.get("category", "unknown")

    # Get user's historical engagement in this category
    category_stats = user.get("category_stats", {}).get(category, {})
    cat_impressions = category_stats.get("impressions", 0)

    if cat_impressions == 0:
        # No history in this category - neutral scores
        cat_like = 0.0
        cat_watch = 0.0
    else:
        # Calculate user's average engagement in this category
        cat_like = category_stats.get("likes", 0) / cat_impressions
        cat_watch = category_stats.get("watch_ratio", 0) / cat_impressions

    # Compute embedding similarity between user profile and video
    emb_sim = cosine_similarity(
        user.get("embedding", []),
        video.get("embedding", [])
    )

    # Weighted combination of category interest and embedding similarity
    interest_score = (
        USER_INTEREST_WEIGHTS["category_watch"] * cat_watch +
        USER_INTEREST_WEIGHTS["category_like"] * cat_like +
        USER_INTEREST_WEIGHTS["embedding_sim"] * emb_sim
    )

    return max(0.0, min(1.0, interest_score))  # Clamp to [0, 1]


# ============================================
# EXPLORATION (UCB-STYLE)
# ============================================

def compute_exploration_bonus(user: Dict[str, Any], video: Dict[str, Any]) -> float:
    """
    Compute exploration bonus using Upper Confidence Bound (UCB) approach.

    This encourages showing videos the user hasn't seen much, promoting discovery.

    Formula: EXPLORATION_COEFF * sqrt(log(total_events + 1) / (video_impressions + 1))

    Args:
        user: User document with total_events and video_history
        video: Video document with _id

    Returns:
        float: Exploration bonus (higher = less explored)
    """
    total_events = user.get("total_events", 1)

    # How many times has this user seen this specific video?
    video_id = str(video.get("id", video.get("_id", "")))
    video_history = user.get("video_history", {})
    user_video_impressions = video_history.get(video_id, 0)

    # UCB formula: higher bonus for unseen videos
    try:
        bonus = EXPLORATION_COEFF * math.sqrt(
            math.log(total_events + 1) / (user_video_impressions + 1)
        )
        return bonus
    except Exception as e:
        logger.warning(f"Error computing exploration bonus: {e}")
        return 0.0


# ============================================
# FINAL RANKING SCORE
# ============================================

def final_score(user: Dict[str, Any], video: Dict[str, Any], now: float) -> float:
    """
    Compute the final ranking score for a (user, video) pair.

    This is the TikTok-style monolithic scoring function that combines:
    1. User interest (personalization)
    2. Video quality (global engagement)
    3. Exploration bonus (discovery)

    Videos that haven't been shown in VIDEO_DEAD_THRESHOLD get filtered out.

    Args:
        user: User document
        video: Video document
        now: Current timestamp (seconds since epoch)

    Returns:
        float: Final ranking score (higher = better match)
               Returns -1e9 for "dead" videos (too old without impressions)
    """
    # Filter out "dead" videos (not shown in X days)
    last_seen = video.get("last_seen_ts", 0)
    if last_seen > 0 and (now - last_seen) > VIDEO_DEAD_THRESHOLD:
        return -1e9

    # Compute component scores
    video_score = compute_video_score(video, now)
    user_score = compute_user_interest(user, video)
    explore_score = compute_exploration_bonus(user, video)

    # Weighted combination
    final = (
        FINAL_SCORE_WEIGHTS["user_interest"] * user_score +
        FINAL_SCORE_WEIGHTS["video_quality"] * video_score +
        FINAL_SCORE_WEIGHTS["exploration"] * explore_score
    )

    return final


# ============================================
# FEED GENERATION
# ============================================

def rank_videos_for_user(
    user: Dict[str, Any],
    candidate_videos: List[Dict[str, Any]],
    limit: int = 20,
    now: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Rank a list of candidate videos for a specific user.

    Args:
        user: User document
        candidate_videos: List of video documents to rank
        limit: Maximum number of videos to return
        now: Current timestamp (defaults to time.time())

    Returns:
        list: Top N videos ranked by score, each with added 'score' field
    """
    if now is None:
        now = time.time()

    # Score each video
    scored_videos = []
    for video in candidate_videos:
        score = final_score(user, video, now)

        # Skip dead videos
        if score <= -1e8:
            continue

        video_with_score = video.copy()
        video_with_score["score"] = score
        scored_videos.append(video_with_score)

    # Sort by score (descending) and take top N
    scored_videos.sort(key=lambda v: v["score"], reverse=True)

    return scored_videos[:limit]


def diversity_rerank(
    ranked_videos: List[Dict[str, Any]],
    diversity_factor: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Apply diversity re-ranking to avoid showing too many similar videos.

    This prevents the feed from being all sports or all comedy.

    Args:
        ranked_videos: Videos already ranked by score
        diversity_factor: How much to penalize consecutive same-category videos (0-1)

    Returns:
        list: Re-ranked videos with better category diversity
    """
    if len(ranked_videos) <= 1:
        return ranked_videos

    reranked = [ranked_videos[0]]  # Always take top video
    remaining = ranked_videos[1:]

    for _ in range(len(remaining)):
        if not remaining:
            break

        # Get last few categories in feed
        recent_categories = [v.get("category", "") for v in reranked[-3:]]

        # Score each remaining video with diversity penalty
        best_idx = 0
        best_score = -1e9

        for idx, video in enumerate(remaining):
            base_score = video.get("score", 0)

            # Penalize if same category as recent videos
            category = video.get("category", "")
            penalty = recent_categories.count(category) * diversity_factor

            adjusted_score = base_score * (1 - penalty)

            if adjusted_score > best_score:
                best_score = adjusted_score
                best_idx = idx

        # Add best video to reranked list
        reranked.append(remaining.pop(best_idx))

    return reranked


# ============================================
# DEBUG & ANALYSIS
# ============================================

def explain_score(user: Dict[str, Any], video: Dict[str, Any], now: Optional[float] = None) -> Dict[str, Any]:
    """
    Return a detailed breakdown of score components for debugging.

    Args:
        user: User document
        video: Video document
        now: Current timestamp (defaults to time.time())

    Returns:
        dict: Score breakdown with all component scores
    """
    if now is None:
        now = time.time()

    video_score = compute_video_score(video, now)
    user_score = compute_user_interest(user, video)
    explore_score = compute_exploration_bonus(user, video)
    total = final_score(user, video, now)

    return {
        "video_id": video.get("id", video.get("_id", "unknown")),
        "video_title": video.get("title", "Untitled"),
        "total_score": total,
        "components": {
            "video_quality": {
                "score": video_score,
                "weight": FINAL_SCORE_WEIGHTS["video_quality"],
                "weighted": video_score * FINAL_SCORE_WEIGHTS["video_quality"],
            },
            "user_interest": {
                "score": user_score,
                "weight": FINAL_SCORE_WEIGHTS["user_interest"],
                "weighted": user_score * FINAL_SCORE_WEIGHTS["user_interest"],
            },
            "exploration": {
                "score": explore_score,
                "weight": FINAL_SCORE_WEIGHTS["exploration"],
                "weighted": explore_score * FINAL_SCORE_WEIGHTS["exploration"],
            },
        },
        "video_stats": video.get("stats", {}),
        "user_category_stats": user.get("category_stats", {}).get(video.get("category", ""), {}),
    }
