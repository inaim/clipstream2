"""
Model Configuration for Different Training Objectives

This module defines different weight configurations for training the video scoring model
with various objectives: engagement, retention, discovery, and monetization.

Each configuration specifies:
- Tower weights (content, interaction, user)
- Feature weights (views, likes, comments, shares)
- Temporal parameters (freshness decay)
- Training hyperparameters
"""

from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    """Configuration for a model training objective."""

    # Model architecture
    clip_embedding_dim: int = 512
    hidden_dim: int = 128
    dropout: float = 0.2

    # Tower weights (relative importance of each signal tower)
    content_weight: float = 0.33
    interaction_weight: float = 0.33
    user_weight: float = 0.33

    # Feature weights (for interaction scoring)
    view_weight: float = 1.0
    like_weight: float = 5.0
    comment_weight: float = 8.0
    share_weight: float = 10.0

    # Temporal parameters
    freshness_decay: float = 24.0  # hours for exponential decay
    watch_time_multiplier: float = 2.0

    # Training hyperparameters
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    weight_decay: float = 1e-5

    # Objective-specific settings
    label_type: str = "engagement"  # 'watch_time', 'engagement', 'retention'
    diversity_factor: float = 0.2  # [0, 1] for inference

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)


# Predefined configurations for different objectives

ENGAGEMENT_CONFIG = ModelConfig(
    # Optimize for maximum user engagement (likes, comments, shares)
    content_weight=0.25,
    interaction_weight=0.50,  # High weight on engagement signals
    user_weight=0.25,

    view_weight=1.0,
    like_weight=8.0,  # High value on likes
    comment_weight=10.0,  # High value on comments
    share_weight=12.0,  # Highest value on shares (strongest signal)

    freshness_decay=24.0,  # Decay over 24 hours
    watch_time_multiplier=1.5,

    label_type="engagement",
    diversity_factor=0.2,

    learning_rate=0.001,
    batch_size=32,
    epochs=15
)


RETENTION_CONFIG = ModelConfig(
    # Optimize for watch time and content quality
    content_weight=0.35,  # Higher content weight
    interaction_weight=0.30,
    user_weight=0.35,  # Higher user preference weight

    view_weight=1.0,
    like_weight=5.0,
    comment_weight=6.0,
    share_weight=7.0,

    freshness_decay=48.0,  # Slower decay - quality over recency
    watch_time_multiplier=3.0,  # Heavy emphasis on watch time

    label_type="retention",
    diversity_factor=0.15,  # Lower diversity, focus on user preferences

    learning_rate=0.0008,
    batch_size=32,
    epochs=20
)


DISCOVERY_CONFIG = ModelConfig(
    # Optimize for content diversity and exploration
    content_weight=0.40,  # Highest content weight
    interaction_weight=0.30,
    user_weight=0.30,

    view_weight=1.0,
    like_weight=4.0,
    comment_weight=5.0,
    share_weight=6.0,

    freshness_decay=12.0,  # Fast decay - prioritize new content
    watch_time_multiplier=1.0,

    label_type="engagement",
    diversity_factor=0.4,  # High diversity for exploration

    learning_rate=0.001,
    batch_size=32,
    epochs=12
)


VIRAL_CONFIG = ModelConfig(
    # Optimize for viral/trending content detection
    content_weight=0.20,
    interaction_weight=0.60,  # Very high interaction weight
    user_weight=0.20,

    view_weight=2.0,  # Higher view weight for virality
    like_weight=10.0,
    comment_weight=12.0,
    share_weight=15.0,  # Shares are strongest viral signal

    freshness_decay=6.0,  # Very fast decay - catch trending early
    watch_time_multiplier=1.5,

    label_type="engagement",
    diversity_factor=0.1,  # Low diversity - focus on what's hot

    learning_rate=0.001,
    batch_size=64,  # Larger batches for stability
    epochs=10
)


MONETIZATION_CONFIG = ModelConfig(
    # Optimize for revenue generation (gifts, watch time)
    content_weight=0.30,
    interaction_weight=0.35,
    user_weight=0.35,  # High user weight for targeting

    view_weight=1.0,
    like_weight=6.0,
    comment_weight=8.0,
    share_weight=10.0,

    freshness_decay=36.0,  # Medium decay
    watch_time_multiplier=2.5,  # High watch time value

    label_type="engagement",
    diversity_factor=0.25,

    learning_rate=0.0009,
    batch_size=32,
    epochs=15
)


BALANCED_CONFIG = ModelConfig(
    # Balanced configuration for general use
    content_weight=0.33,
    interaction_weight=0.33,
    user_weight=0.33,

    view_weight=1.0,
    like_weight=5.0,
    comment_weight=8.0,
    share_weight=10.0,

    freshness_decay=24.0,
    watch_time_multiplier=2.0,

    label_type="engagement",
    diversity_factor=0.2,

    learning_rate=0.001,
    batch_size=32,
    epochs=10
)


# Configuration registry
CONFIGS = {
    'engagement': ENGAGEMENT_CONFIG,
    'retention': RETENTION_CONFIG,
    'discovery': DISCOVERY_CONFIG,
    'viral': VIRAL_CONFIG,
    'monetization': MONETIZATION_CONFIG,
    'balanced': BALANCED_CONFIG
}


def get_config(objective: str) -> ModelConfig:
    """
    Get configuration for a specific objective.

    Args:
        objective: One of 'engagement', 'retention', 'discovery', 'viral', 'monetization', 'balanced'

    Returns:
        config: ModelConfig instance

    Raises:
        ValueError: If objective is not recognized
    """
    if objective not in CONFIGS:
        raise ValueError(
            f"Unknown objective '{objective}'. "
            f"Available: {list(CONFIGS.keys())}"
        )

    return CONFIGS[objective]


def list_objectives() -> list:
    """List all available objective configurations."""
    return list(CONFIGS.keys())


def create_custom_config(**kwargs) -> ModelConfig:
    """
    Create a custom configuration.

    Args:
        **kwargs: Any ModelConfig parameters to override

    Returns:
        config: Custom ModelConfig instance

    Example:
        >>> config = create_custom_config(
        ...     content_weight=0.4,
        ...     interaction_weight=0.6,
        ...     learning_rate=0.002
        ... )
    """
    return ModelConfig(**kwargs)


# A/B Test Configurations
# These are slight variations for A/B testing different hypotheses

AB_TEST_CONFIGS = {
    'high_content': create_custom_config(
        content_weight=0.5,
        interaction_weight=0.3,
        user_weight=0.2
    ),
    'high_user': create_custom_config(
        content_weight=0.2,
        interaction_weight=0.3,
        user_weight=0.5
    ),
    'high_freshness': create_custom_config(
        freshness_decay=6.0
    ),
    'low_freshness': create_custom_config(
        freshness_decay=72.0
    ),
    'high_diversity': create_custom_config(
        diversity_factor=0.5
    ),
    'low_diversity': create_custom_config(
        diversity_factor=0.05
    )
}


def get_ab_config(variant: str) -> ModelConfig:
    """
    Get A/B test configuration variant.

    Args:
        variant: A/B test variant name

    Returns:
        config: ModelConfig for the variant
    """
    if variant not in AB_TEST_CONFIGS:
        raise ValueError(
            f"Unknown A/B variant '{variant}'. "
            f"Available: {list(AB_TEST_CONFIGS.keys())}"
        )

    return AB_TEST_CONFIGS[variant]
