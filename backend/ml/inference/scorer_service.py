"""
Video Scoring Inference Service

Provides real-time video scoring for personalized recommendations using trained AI models.
This service loads trained models and scores videos for each user based on:
- Video content features
- User interaction history
- Current trending signals
- Personalization preferences
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import asyncio

from ..models.video_scorer import VideoScoringModel, MultiObjectiveVideoScorer
from ..features.feature_engineering import BatchFeatureExtractor

logger = logging.getLogger(__name__)


class VideoScorerService:
    """
    Production inference service for video scoring.

    Loads trained models and provides fast scoring for video recommendations.
    Supports multiple objectives and A/B testing different model weights.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_type: str = 'single',
        device: str = 'cpu',
        batch_size: int = 50
    ):
        """
        Initialize the scoring service.

        Args:
            model_path: Path to trained model checkpoint
            model_type: 'single' or 'multi_objective'
            device: 'cpu' or 'cuda'
            batch_size: Batch size for inference
        """
        self.device = torch.device(device)
        self.model_type = model_type
        self.batch_size = batch_size

        # Load model
        if model_path and Path(model_path).exists():
            self.model = self._load_model(model_path)
        else:
            # Initialize with default weights if no model provided
            logger.warning("No model path provided, using untrained model")
            if model_type == 'single':
                self.model = VideoScoringModel().to(self.device)
            else:
                self.model = MultiObjectiveVideoScorer().to(self.device)

        self.model.eval()

        # Feature extractor
        self.feature_extractor = BatchFeatureExtractor()

        # Cache for user features (optional optimization)
        self.user_feature_cache = {}

        logger.info(f"VideoScorerService initialized with {model_type} model on {device}")

    def _load_model(self, model_path: str):
        """Load trained model from checkpoint."""
        logger.info(f"Loading model from {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device)

        if self.model_type == 'single':
            model = VideoScoringModel(
                weight_config=checkpoint.get('weight_config')
            ).to(self.device)
        else:
            model = MultiObjectiveVideoScorer().to(self.device)

        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        logger.info("Model loaded successfully")
        return model

    async def score_videos(
        self,
        videos: List[Dict],
        user_data: Dict,
        user_history: Optional[List[Dict]] = None,
        objective: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Score a list of videos for a user.

        Args:
            videos: List of video dicts
            user_data: User profile and stats
            user_history: Optional user interaction history
            objective: Optional objective for multi-objective models

        Returns:
            scored_videos: List of (video_id, score) tuples sorted by score descending
        """
        if not videos:
            return []

        # Extract features for all videos
        clip_embeddings, interaction_features, user_features = self.feature_extractor.extract_batch(
            videos=videos,
            user_data=user_data,
            user_history=user_history
        )

        # Convert to tensors
        clip_embeddings = torch.from_numpy(clip_embeddings).to(self.device)
        interaction_features = torch.from_numpy(interaction_features).to(self.device)
        user_features = torch.from_numpy(user_features).to(self.device)

        # Score in batches
        all_scores = []

        with torch.no_grad():
            for i in range(0, len(videos), self.batch_size):
                batch_clip = clip_embeddings[i:i + self.batch_size]
                batch_inter = interaction_features[i:i + self.batch_size]
                batch_user = user_features[i:i + self.batch_size]

                if self.model_type == 'multi_objective' and objective:
                    scores = self.model(batch_clip, batch_inter, batch_user, objective=objective)
                else:
                    scores = self.model(batch_clip, batch_inter, batch_user)

                all_scores.append(scores.cpu().numpy())

        # Concatenate all batch scores
        all_scores = np.concatenate(all_scores, axis=0).flatten()

        # Create (video_id, score) pairs
        scored_videos = [
            (video['id'], float(score))
            for video, score in zip(videos, all_scores)
        ]

        # Sort by score descending
        scored_videos.sort(key=lambda x: x[1], reverse=True)

        return scored_videos

    async def rank_feed(
        self,
        candidate_videos: List[Dict],
        user_data: Dict,
        user_history: Optional[List[Dict]] = None,
        limit: int = 50,
        objective: Optional[str] = None,
        diversity_factor: float = 0.0
    ) -> List[Dict]:
        """
        Rank videos for a user's feed.

        Args:
            candidate_videos: Videos to rank
            user_data: User profile
            user_history: User interaction history
            limit: Number of videos to return
            objective: Optional objective (engagement, retention, etc.)
            diversity_factor: [0, 1] factor for diversity boost (0 = pure relevance)

        Returns:
            ranked_videos: Top videos sorted by score
        """
        # Score all candidates
        scored_videos = await self.score_videos(
            videos=candidate_videos,
            user_data=user_data,
            user_history=user_history,
            objective=objective
        )

        # Apply diversity if needed
        if diversity_factor > 0:
            scored_videos = self._apply_diversity(
                scored_videos,
                candidate_videos,
                diversity_factor
            )

        # Get top videos
        top_video_ids = [vid_id for vid_id, _ in scored_videos[:limit]]

        # Create lookup dict
        video_dict = {v['id']: v for v in candidate_videos}

        # Return ranked videos
        ranked_videos = [
            video_dict[vid_id]
            for vid_id in top_video_ids
            if vid_id in video_dict
        ]

        return ranked_videos

    def _apply_diversity(
        self,
        scored_videos: List[Tuple[str, float]],
        all_videos: List[Dict],
        diversity_factor: float
    ) -> List[Tuple[str, float]]:
        """
        Apply diversity boost to prevent filter bubble.

        Uses a simple creator diversity heuristic:
        - Boost videos from creators not in top positions
        - Maintain balance between relevance and diversity

        Args:
            scored_videos: List of (video_id, score) tuples
            all_videos: All video dicts
            diversity_factor: [0, 1] diversity weight

        Returns:
            diversified_scores: Reranked list
        """
        video_dict = {v['id']: v for v in all_videos}
        creator_counts = {}

        diversified = []

        for video_id, score in scored_videos:
            video = video_dict.get(video_id)
            if not video:
                continue

            creator_id = video.get('user_id', 'unknown')

            # Diversity penalty based on how many videos from this creator are already ranked
            creator_count = creator_counts.get(creator_id, 0)
            diversity_penalty = creator_count * diversity_factor * 0.1

            # Adjusted score
            adjusted_score = score - diversity_penalty

            diversified.append((video_id, adjusted_score))

            # Update creator count
            creator_counts[creator_id] = creator_count + 1

        # Re-sort by adjusted scores
        diversified.sort(key=lambda x: x[1], reverse=True)

        return diversified

    async def score_single_video(
        self,
        video: Dict,
        user_data: Dict,
        user_history: Optional[List[Dict]] = None,
        objective: Optional[str] = None
    ) -> float:
        """
        Score a single video for a user.

        Args:
            video: Video dict
            user_data: User profile
            user_history: User interaction history
            objective: Optional objective

        Returns:
            score: Predicted score for the video
        """
        scored = await self.score_videos(
            videos=[video],
            user_data=user_data,
            user_history=user_history,
            objective=objective
        )

        if scored:
            return scored[0][1]
        return 0.0

    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        info = {
            "model_type": self.model_type,
            "device": str(self.device),
            "batch_size": self.batch_size
        }

        # Add tower weights for single objective model
        if self.model_type == 'single' and hasattr(self.model, 'get_tower_weights'):
            info['tower_weights'] = self.model.get_tower_weights()

        return info


class MultiModelService:
    """
    Service that manages multiple models for A/B testing.

    Allows running different model variants in parallel to compare performance.
    """

    def __init__(self, device: str = 'cpu'):
        self.device = device
        self.models = {}

    def add_model(
        self,
        model_name: str,
        model_path: str,
        model_type: str = 'single'
    ):
        """
        Add a model variant.

        Args:
            model_name: Identifier for this model (e.g., 'engagement_v1', 'retention_v2')
            model_path: Path to model checkpoint
            model_type: Model type
        """
        service = VideoScorerService(
            model_path=model_path,
            model_type=model_type,
            device=self.device
        )
        self.models[model_name] = service
        logger.info(f"Added model '{model_name}' from {model_path}")

    async def score_with_model(
        self,
        model_name: str,
        videos: List[Dict],
        user_data: Dict,
        user_history: Optional[List[Dict]] = None,
        objective: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Score videos using a specific model variant.

        Args:
            model_name: Which model to use
            videos: Videos to score
            user_data: User data
            user_history: User history
            objective: Optional objective

        Returns:
            scored_videos: Scored and sorted videos
        """
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")

        service = self.models[model_name]
        return await service.score_videos(
            videos=videos,
            user_data=user_data,
            user_history=user_history,
            objective=objective
        )

    def list_models(self) -> List[str]:
        """List all available models."""
        return list(self.models.keys())


# Global service instance (singleton)
_scorer_service: Optional[VideoScorerService] = None


def get_scorer_service() -> VideoScorerService:
    """
    Get the global scorer service instance.

    Returns:
        service: VideoScorerService instance
    """
    global _scorer_service
    if _scorer_service is None:
        # Initialize with default model
        # In production, this would load from config
        _scorer_service = VideoScorerService(
            model_path=None,  # Will use untrained model initially
            device='cpu'
        )
    return _scorer_service


def set_scorer_service(service: VideoScorerService):
    """
    Set the global scorer service instance.

    Args:
        service: Configured VideoScorerService
    """
    global _scorer_service
    _scorer_service = service
    logger.info("Global scorer service updated")
