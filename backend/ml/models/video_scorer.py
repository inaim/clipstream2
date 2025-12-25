"""
AI-based Video Scoring Model

This module implements a neural network model for scoring videos based on:
- Video content features (CLIP embeddings, metadata)
- User interaction patterns (views, likes, comments, shares)
- Temporal features (freshness, trending signals)
- User preferences and behavior

The model is designed to be trainable with different weight configurations
for different ranking objectives (engagement, retention, discovery, etc.)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple
import numpy as np


class VideoScoringModel(nn.Module):
    """
    Neural network model for video scoring with configurable weights.

    Architecture:
    - Content Tower: Processes video features (CLIP embeddings, metadata)
    - Interaction Tower: Processes user engagement signals
    - User Tower: Processes user preferences and history
    - Fusion Layer: Combines all signals with learned weights
    - Output: Single score for ranking
    """

    def __init__(
        self,
        clip_embedding_dim: int = 512,
        content_feature_dim: int = 32,
        interaction_feature_dim: int = 16,
        user_feature_dim: int = 64,
        hidden_dim: int = 128,
        dropout: float = 0.2,
        weight_config: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the video scoring model.

        Args:
            clip_embedding_dim: Dimension of CLIP video embeddings (default: 512)
            content_feature_dim: Dimension for processed content features
            interaction_feature_dim: Dimension for interaction features
            user_feature_dim: Dimension for user preference features
            hidden_dim: Hidden layer dimension
            dropout: Dropout rate for regularization
            weight_config: Optional dict with feature weights for different objectives
        """
        super(VideoScoringModel, self).__init__()

        # Store configuration
        self.clip_embedding_dim = clip_embedding_dim
        self.weight_config = weight_config or self._default_weights()

        # Content Tower - Processes video features
        self.content_tower = nn.Sequential(
            nn.Linear(clip_embedding_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, content_feature_dim),
            nn.ReLU()
        )

        # Interaction Tower - Processes engagement signals
        # Input: [view_count, like_count, comment_count, share_count,
        #         watch_time_ratio, engagement_rate, virality_score, freshness]
        self.interaction_tower = nn.Sequential(
            nn.Linear(8, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, interaction_feature_dim),
            nn.ReLU()
        )

        # User Tower - Processes user preferences
        # Input: [user_avg_watch_time, user_interaction_rate, category_preference,
        #         creator_affinity, temporal_pattern, diversity_score]
        self.user_tower = nn.Sequential(
            nn.Linear(6, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, user_feature_dim),
            nn.ReLU()
        )

        # Fusion Layer - Combines all towers
        fusion_input_dim = content_feature_dim + interaction_feature_dim + user_feature_dim
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )

        # Learnable weights for tower outputs (initialized from config)
        self.tower_weights = nn.Parameter(
            torch.tensor([
                self.weight_config['content_weight'],
                self.weight_config['interaction_weight'],
                self.weight_config['user_weight']
            ])
        )

    def _default_weights(self) -> Dict[str, float]:
        """Default weight configuration for balanced scoring."""
        return {
            'content_weight': 0.3,
            'interaction_weight': 0.4,
            'user_weight': 0.3,
            'view_weight': 1.0,
            'like_weight': 5.0,
            'comment_weight': 8.0,
            'share_weight': 10.0,
            'freshness_decay': 24.0  # hours
        }

    def forward(
        self,
        clip_embeddings: torch.Tensor,
        interaction_features: torch.Tensor,
        user_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass through the model.

        Args:
            clip_embeddings: [batch_size, 512] - CLIP video embeddings
            interaction_features: [batch_size, 8] - Engagement metrics
            user_features: [batch_size, 6] - User preference features

        Returns:
            scores: [batch_size, 1] - Predicted video scores
        """
        # Process through towers
        content_repr = self.content_tower(clip_embeddings)
        interaction_repr = self.interaction_tower(interaction_features)
        user_repr = self.user_tower(user_features)

        # Apply learnable tower weights
        normalized_weights = F.softmax(self.tower_weights, dim=0)

        weighted_content = content_repr * normalized_weights[0]
        weighted_interaction = interaction_repr * normalized_weights[1]
        weighted_user = user_repr * normalized_weights[2]

        # Concatenate weighted representations
        fused_features = torch.cat([
            weighted_content,
            weighted_interaction,
            weighted_user
        ], dim=1)

        # Final scoring
        scores = self.fusion_layer(fused_features)

        return scores

    def get_tower_weights(self) -> Dict[str, float]:
        """Get current tower weight values."""
        weights = F.softmax(self.tower_weights, dim=0).detach().cpu().numpy()
        return {
            'content': float(weights[0]),
            'interaction': float(weights[1]),
            'user': float(weights[2])
        }


class MultiObjectiveVideoScorer(nn.Module):
    """
    Multi-objective scoring model that can optimize for different goals:
    - Engagement: Maximize likes, comments, shares
    - Retention: Maximize watch time
    - Discovery: Balance between popular and diverse content
    - Monetization: Optimize for gift revenue

    This model has multiple heads for different objectives and can be
    trained with different weight configurations.
    """

    def __init__(
        self,
        clip_embedding_dim: int = 512,
        hidden_dim: int = 128,
        dropout: float = 0.2,
        num_objectives: int = 4
    ):
        super(MultiObjectiveVideoScorer, self).__init__()

        # Shared encoder
        self.shared_encoder = nn.Sequential(
            nn.Linear(clip_embedding_dim + 8 + 6, hidden_dim * 2),
            nn.LayerNorm(hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Objective-specific heads
        self.engagement_head = nn.Linear(hidden_dim, 1)
        self.retention_head = nn.Linear(hidden_dim, 1)
        self.discovery_head = nn.Linear(hidden_dim, 1)
        self.monetization_head = nn.Linear(hidden_dim, 1)

        # Learnable objective weights
        self.objective_weights = nn.Parameter(
            torch.ones(num_objectives) / num_objectives
        )

    def forward(
        self,
        clip_embeddings: torch.Tensor,
        interaction_features: torch.Tensor,
        user_features: torch.Tensor,
        objective: Optional[str] = None
    ) -> torch.Tensor:
        """
        Forward pass with optional objective selection.

        Args:
            clip_embeddings: [batch_size, 512]
            interaction_features: [batch_size, 8]
            user_features: [batch_size, 6]
            objective: Optional objective name ('engagement', 'retention', etc.)
                      If None, uses weighted combination of all objectives

        Returns:
            scores: [batch_size, 1]
        """
        # Concatenate all features
        combined_features = torch.cat([
            clip_embeddings,
            interaction_features,
            user_features
        ], dim=1)

        # Shared encoding
        encoded = self.shared_encoder(combined_features)

        # Compute all objective scores
        engagement_score = self.engagement_head(encoded)
        retention_score = self.retention_head(encoded)
        discovery_score = self.discovery_head(encoded)
        monetization_score = self.monetization_head(encoded)

        # Select output based on objective
        if objective == 'engagement':
            return engagement_score
        elif objective == 'retention':
            return retention_score
        elif objective == 'discovery':
            return discovery_score
        elif objective == 'monetization':
            return monetization_score
        else:
            # Weighted combination of all objectives
            weights = F.softmax(self.objective_weights, dim=0)
            combined_score = (
                weights[0] * engagement_score +
                weights[1] * retention_score +
                weights[2] * discovery_score +
                weights[3] * monetization_score
            )
            return combined_score

    def get_all_scores(
        self,
        clip_embeddings: torch.Tensor,
        interaction_features: torch.Tensor,
        user_features: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """Get scores for all objectives separately."""
        combined_features = torch.cat([
            clip_embeddings,
            interaction_features,
            user_features
        ], dim=1)

        encoded = self.shared_encoder(combined_features)

        return {
            'engagement': self.engagement_head(encoded),
            'retention': self.retention_head(encoded),
            'discovery': self.discovery_head(encoded),
            'monetization': self.monetization_head(encoded)
        }
