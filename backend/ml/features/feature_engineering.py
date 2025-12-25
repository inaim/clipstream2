"""
Feature Engineering for Video Scoring Model

This module extracts and processes features from:
- Video content (CLIP embeddings, metadata)
- User interactions (views, likes, comments, shares, watch time)
- User preferences and behavior patterns
- Temporal signals (freshness, trending)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math


class VideoFeatureExtractor:
    """Extracts features from video data for the scoring model."""

    def __init__(self, weight_config: Optional[Dict[str, float]] = None):
        """
        Initialize feature extractor.

        Args:
            weight_config: Optional configuration for feature weights
        """
        self.weight_config = weight_config or self._default_weights()

    def _default_weights(self) -> Dict[str, float]:
        """Default feature weights."""
        return {
            'view_weight': 1.0,
            'like_weight': 5.0,
            'comment_weight': 8.0,
            'share_weight': 10.0,
            'freshness_decay': 24.0,  # hours
            'watch_time_multiplier': 2.0
        }

    def extract_clip_embeddings(self, video_data: Dict) -> np.ndarray:
        """
        Extract or prepare CLIP embeddings for a video.

        Args:
            video_data: Dict containing video information

        Returns:
            clip_embedding: (512,) array, zero-filled if not available
        """
        if 'clip_embedding' in video_data and video_data['clip_embedding']:
            embedding = np.array(video_data['clip_embedding'], dtype=np.float32)
            # Normalize embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding
        else:
            # Return zero embedding if not available
            # In production, this should trigger embedding generation
            return np.zeros(512, dtype=np.float32)

    def extract_interaction_features(self, video_data: Dict) -> np.ndarray:
        """
        Extract interaction-based features from video data.

        Features:
        1. view_count (normalized log scale)
        2. like_count (normalized log scale)
        3. comment_count (normalized log scale)
        4. share_count (normalized log scale)
        5. watch_time_ratio (avg watch time / duration)
        6. engagement_rate ((likes + comments + shares) / views)
        7. virality_score (existing or computed)
        8. freshness (time-based decay factor)

        Args:
            video_data: Dict with video metrics

        Returns:
            features: (8,) array of interaction features
        """
        # Extract counts with safe defaults
        view_count = float(video_data.get('view_count', 0))
        like_count = float(video_data.get('like_count', 0))
        comment_count = float(video_data.get('comment_count', 0))
        share_count = float(video_data.get('share_count', 0))
        duration = float(video_data.get('duration', 1))  # seconds

        # Compute derived metrics
        avg_watch_time = video_data.get('avg_watch_time', duration * 0.5)
        watch_time_ratio = min(1.0, avg_watch_time / duration) if duration > 0 else 0.0

        # Engagement rate
        if view_count > 0:
            engagement_rate = (like_count + comment_count + share_count) / view_count
        else:
            engagement_rate = 0.0

        # Virality score (use existing or compute)
        virality_score = video_data.get('virality_score', 0.0)
        if virality_score == 0.0 and view_count > 0:
            virality_score = self._compute_virality_score(video_data)

        # Freshness factor (exponential decay based on age)
        freshness = self._compute_freshness(video_data)

        # Normalize counts using log1p for better distribution
        features = np.array([
            np.log1p(view_count) / 10.0,  # Scaled log views
            np.log1p(like_count) / 8.0,  # Scaled log likes
            np.log1p(comment_count) / 6.0,  # Scaled log comments
            np.log1p(share_count) / 5.0,  # Scaled log shares
            watch_time_ratio,  # [0, 1]
            min(1.0, engagement_rate),  # Capped at 1.0
            virality_score / 100.0,  # Normalized virality
            freshness  # [0, 1] time decay
        ], dtype=np.float32)

        return features

    def extract_user_features(
        self,
        user_data: Dict,
        video_data: Dict,
        user_history: Optional[List[Dict]] = None
    ) -> np.ndarray:
        """
        Extract user preference and behavior features.

        Features:
        1. user_avg_watch_time (normalized)
        2. user_interaction_rate (historical engagement)
        3. category_preference (user affinity for video category)
        4. creator_affinity (has liked/followed creator before)
        5. temporal_pattern (matches user's active hours)
        6. diversity_score (exploration vs exploitation)

        Args:
            user_data: User profile and stats
            video_data: Current video being scored
            user_history: Optional list of user's interaction history

        Returns:
            features: (6,) array of user features
        """
        user_history = user_history or []

        # User's average watch time pattern
        if user_history:
            watch_times = [h.get('watch_time', 0) for h in user_history]
            user_avg_watch_time = np.mean(watch_times) if watch_times else 30.0
        else:
            user_avg_watch_time = 30.0  # Default 30 seconds

        # Normalize by typical video duration (60s)
        normalized_watch_time = min(1.0, user_avg_watch_time / 60.0)

        # User's interaction rate
        if user_history:
            interactions = sum(
                1 for h in user_history
                if h.get('liked') or h.get('commented') or h.get('shared')
            )
            user_interaction_rate = interactions / len(user_history)
        else:
            user_interaction_rate = 0.1  # Default low engagement

        # Category preference (based on hashtags)
        video_hashtags = set(video_data.get('hashtags', []))
        if user_history and video_hashtags:
            user_hashtags = set()
            for hist in user_history:
                user_hashtags.update(hist.get('hashtags', []))

            overlap = len(video_hashtags.intersection(user_hashtags))
            category_preference = min(1.0, overlap / max(1, len(video_hashtags)))
        else:
            category_preference = 0.5  # Neutral

        # Creator affinity
        creator_id = video_data.get('user_id')
        creator_affinity = 0.0
        if user_history and creator_id:
            creator_interactions = sum(
                1 for h in user_history if h.get('creator_id') == creator_id
            )
            creator_affinity = min(1.0, creator_interactions / 5.0)  # Max at 5 interactions

        # Temporal pattern (simplified - could be expanded with hourly patterns)
        current_hour = datetime.now().hour
        user_active_hours = user_data.get('active_hours', [current_hour])
        temporal_pattern = 1.0 if current_hour in user_active_hours else 0.5

        # Diversity score (explore vs exploit)
        # Higher score = show more diverse content
        if user_history:
            recent_creators = set(h.get('creator_id') for h in user_history[-20:])
            diversity_score = min(1.0, len(recent_creators) / 20.0)
        else:
            diversity_score = 1.0  # New users get diverse content

        features = np.array([
            normalized_watch_time,
            user_interaction_rate,
            category_preference,
            creator_affinity,
            temporal_pattern,
            diversity_score
        ], dtype=np.float32)

        return features

    def _compute_virality_score(self, video_data: Dict) -> float:
        """
        Compute virality score based on engagement velocity.

        Score = (views_per_hour * 1.0 +
                 likes_per_hour * 5.0 +
                 shares_per_hour * 10.0 +
                 comments_per_hour * 8.0) * exp(-age_hours / 24)
        """
        created_at = video_data.get('created_at')
        if not created_at:
            return 0.0

        # Parse datetime
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        age_hours = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600.0
        age_hours = max(0.1, age_hours)  # Avoid division by zero

        # Compute per-hour rates
        views_per_hour = video_data.get('view_count', 0) / age_hours
        likes_per_hour = video_data.get('like_count', 0) / age_hours
        comments_per_hour = video_data.get('comment_count', 0) / age_hours
        shares_per_hour = video_data.get('share_count', 0) / age_hours

        # Weighted score with time decay
        score = (
            views_per_hour * self.weight_config['view_weight'] +
            likes_per_hour * self.weight_config['like_weight'] +
            comments_per_hour * self.weight_config['comment_weight'] +
            shares_per_hour * self.weight_config['share_weight']
        ) * math.exp(-age_hours / self.weight_config['freshness_decay'])

        return float(score)

    def _compute_freshness(self, video_data: Dict) -> float:
        """
        Compute freshness factor using exponential decay.

        Returns value in [0, 1] where 1 is brand new, decaying over time.
        """
        created_at = video_data.get('created_at')
        if not created_at:
            return 0.5  # Default medium freshness

        # Parse datetime
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        age_hours = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600.0

        # Exponential decay with half-life of freshness_decay hours
        decay_rate = self.weight_config['freshness_decay']
        freshness = math.exp(-age_hours / decay_rate)

        return float(freshness)

    def extract_all_features(
        self,
        video_data: Dict,
        user_data: Dict,
        user_history: Optional[List[Dict]] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract all features for a video-user pair.

        Args:
            video_data: Video information
            user_data: User information
            user_history: Optional user interaction history

        Returns:
            clip_embeddings: (512,) array
            interaction_features: (8,) array
            user_features: (6,) array
        """
        clip_embeddings = self.extract_clip_embeddings(video_data)
        interaction_features = self.extract_interaction_features(video_data)
        user_features = self.extract_user_features(user_data, video_data, user_history)

        return clip_embeddings, interaction_features, user_features


class BatchFeatureExtractor:
    """Efficiently extract features for batches of videos."""

    def __init__(self, weight_config: Optional[Dict[str, float]] = None):
        self.extractor = VideoFeatureExtractor(weight_config)

    def extract_batch(
        self,
        videos: List[Dict],
        user_data: Dict,
        user_history: Optional[List[Dict]] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract features for a batch of videos for a single user.

        Args:
            videos: List of video dicts
            user_data: User information
            user_history: Optional user interaction history

        Returns:
            clip_embeddings: (batch_size, 512) array
            interaction_features: (batch_size, 8) array
            user_features: (batch_size, 6) array
        """
        batch_size = len(videos)

        clip_embeddings = np.zeros((batch_size, 512), dtype=np.float32)
        interaction_features = np.zeros((batch_size, 8), dtype=np.float32)
        user_features = np.zeros((batch_size, 6), dtype=np.float32)

        for i, video in enumerate(videos):
            clip_emb, inter_feat, user_feat = self.extractor.extract_all_features(
                video, user_data, user_history
            )
            clip_embeddings[i] = clip_emb
            interaction_features[i] = inter_feat
            user_features[i] = user_feat

        return clip_embeddings, interaction_features, user_features
