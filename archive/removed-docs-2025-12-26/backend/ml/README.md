# AI-Based Video Scoring System

A TikTok-style AI recommendation system that learns from user interactions to personalize video feeds and detect viral content.

## Overview

This ML system provides:

- **Neural network models** for video scoring with configurable weights
- **Event-based training** from real user interactions (views, likes, skips, etc.)
- **Multiple objectives**: engagement, retention, discovery, virality, monetization
- **Real-time inference** for personalized feed ranking
- **Virality detection** for trending content
- **A/B testing** support with multiple model variants

## Architecture

```
ml/
├── models/               # Neural network architectures
│   └── video_scorer.py  # VideoScoringModel, MultiObjectiveVideoScorer
├── features/            # Feature engineering
│   └── feature_engineering.py  # Extract features from videos/users
├── training/            # Model training
│   └── train_scorer.py  # Training scripts with configurable objectives
├── inference/           # Production inference
│   └── scorer_service.py  # Fast video scoring service
├── events/              # Event recording
│   └── video_events.py  # Track user interactions for training
├── config/              # Model configurations
│   └── model_configs.py  # Weight presets for different objectives
└── evaluation/          # Metrics and monitoring
    └── metrics.py       # Ranking metrics, A/B testing
```

## Quick Start

### 1. Record User Events

```python
from ml.events import VideoEventRecorder, EventType

event_recorder = VideoEventRecorder(db_client)

# Record a view
await event_recorder.record_view(
    video_id="video:123",
    user_id="user:456",
    source="for_you"
)

# Record watch time
await event_recorder.record_watch(
    video_id="video:123",
    user_id="user:456",
    watch_time=45.0,
    video_duration=60.0
)

# Record engagement
await event_recorder.record_engagement(
    event_type=EventType.LIKE,
    video_id="video:123",
    user_id="user:456"
)

# Record negative signals
await event_recorder.record_skip(
    video_id="video:789",
    user_id="user:456",
    watch_time=2.0,
    video_duration=60.0,
    reason="not_interested"
)
```

### 2. Train a Model

```python
from ml.training import VideoScorerTrainer, create_training_config
from ml.config import get_config

# Load configuration for objective
config = get_config('engagement')  # or 'retention', 'viral', etc.

# Initialize trainer
trainer = VideoScorerTrainer(
    model_type='single',
    weight_config=config.to_dict(),
    learning_rate=config.learning_rate
)

# Train model (assuming you have loaded training data from events)
trainer.train(
    train_dataset=train_dataset,
    val_dataset=val_dataset,
    epochs=config.epochs,
    batch_size=config.batch_size,
    save_dir='./models/checkpoints'
)
```

### 3. Use for Inference

```python
from ml.inference import VideoScorerService

# Initialize service with trained model
scorer = VideoScorerService(
    model_path='./models/checkpoints/best_model.pt',
    device='cpu'
)

# Rank videos for a user
ranked_videos = await scorer.rank_feed(
    candidate_videos=videos,
    user_data=user_profile,
    user_history=user_interaction_history,
    limit=50,
    objective='engagement',
    diversity_factor=0.2
)
```

### 4. Detect Viral Content

```python
from ml.events import VideoEventRecorder

event_recorder = VideoEventRecorder(db_client)

# Get virality metrics for a video
virality = await event_recorder.compute_virality_metrics("video:123")

print(f"Is viral: {virality['is_viral']}")
print(f"Velocity: {virality['velocity']} views/hour")
print(f"Engagement rate: {virality['engagement_rate']}")
```

## Model Configurations

Six pre-configured objectives optimized for different goals:

### 1. Engagement (Default)
- **Goal**: Maximize likes, comments, shares
- **Weights**: High interaction weight (50%), medium content (25%), medium user (25%)
- **Use case**: Viral content, social engagement

### 2. Retention
- **Goal**: Maximize watch time and completion rate
- **Weights**: High content (35%), high user (35%), medium interaction (30%)
- **Use case**: Long-form content, quality over virality

### 3. Discovery
- **Goal**: Show diverse, new content to users
- **Weights**: High content (40%), high diversity (40%)
- **Use case**: Exploration, breaking filter bubbles

### 4. Viral
- **Goal**: Detect and amplify trending content
- **Weights**: Very high interaction (60%), fast freshness decay (6h)
- **Use case**: Trending feed, viral detection

### 5. Monetization
- **Goal**: Optimize for revenue (gifts, watch time)
- **Weights**: Balanced with high user targeting (35%)
- **Use case**: Creator monetization, ad revenue

### 6. Balanced
- **Goal**: General-purpose recommendation
- **Weights**: Equal towers (33% each)
- **Use case**: Default for-you feed

## Event Types

The system tracks both **positive** and **negative** signals:

### Positive Signals
- `VIEW`: Video impression
- `WATCH`: Significant watch time (>10% of video)
- `COMPLETE`: Watched to end (>95%)
- `LIKE`: User liked video
- `COMMENT`: User commented
- `SHARE`: User shared video
- `FOLLOW_FROM_VIDEO`: Followed creator from video
- `GIFT`: Sent gift to creator
- `SAVE`: Saved video
- `REPLAY`: Replayed video

### Negative Signals
- `SKIP`: Quick scroll (<3s or <10%)
- `DISMISS`: Actively dismissed
- `NOT_INTERESTED`: Marked as not interested
- `REPORT`: Reported content
- `BLOCK_CREATOR`: Blocked creator

## Features Extracted

### Video Features (512-dimensional)
- CLIP embeddings (semantic content)
- Duration, resolution, file size
- Hashtags and category

### Interaction Features (8-dimensional)
1. View count (log normalized)
2. Like count (log normalized)
3. Comment count (log normalized)
4. Share count (log normalized)
5. Watch time ratio (avg watch / duration)
6. Engagement rate ((likes + comments + shares) / views)
7. Virality score (weighted engagement velocity)
8. Freshness (exponential time decay)

### User Features (6-dimensional)
1. User avg watch time pattern
2. User interaction rate (historical engagement)
3. Category preference (hashtag affinity)
4. Creator affinity (past interactions with creator)
5. Temporal pattern (active hours match)
6. Diversity score (exploration vs exploitation)

## API Integration

The feed API automatically uses AI scoring when available:

```bash
# Personalized For You feed with AI ranking
GET /api/v1/feed/for-you?user_id=user:123&use_ai=true&limit=50

# Trending feed with virality detection
GET /api/v1/feed/trending?use_ai=true&limit=50
```

## Training Data Pipeline

1. **Event Collection**: Record all user interactions via `VideoEventRecorder`
2. **Feature Extraction**: Convert events to training samples with `VideoFeatureExtractor`
3. **Dataset Creation**: Build `VideoInteractionDataset` from events
4. **Model Training**: Train with `VideoScorerTrainer` using chosen objective
5. **Evaluation**: Validate with ranking metrics (NDCG@10, MRR, Precision@K)
6. **Deployment**: Load trained model in `VideoScorerService` for production

## Evaluation Metrics

### Ranking Metrics
- **NDCG@K**: Normalized Discounted Cumulative Gain
- **MRR**: Mean Reciprocal Rank
- **Precision@K**: Fraction of top K that are relevant
- **Recall@K**: Fraction of relevant items in top K

### Engagement Metrics
- **CTR**: Click-through rate
- **Completion Rate**: Fraction of videos watched to end
- **Engagement Rate**: (likes + comments + shares) / views
- **Watch Time Ratio**: Avg watch time / duration

## A/B Testing

Run multiple model variants in production:

```python
from ml.inference import MultiModelService

service = MultiModelService()

# Add model variants
service.add_model('engagement_v1', './models/engagement_v1.pt')
service.add_model('retention_v2', './models/retention_v2.pt')

# Score with specific variant
scores = await service.score_with_model(
    model_name='engagement_v1',
    videos=videos,
    user_data=user_data
)
```

## Production Monitoring

```python
from ml.evaluation import ProductionMonitor

monitor = ProductionMonitor(db_client)

# Get recent metrics
metrics = await monitor.get_recent_metrics(hours=24)

# Detect anomalies
anomalies = await monitor.detect_anomalies(
    current_metrics=metrics,
    baseline_metrics=baseline,
    threshold=0.2  # 20% change threshold
)
```

## Requirements

```
torch>=2.0.0
numpy>=1.24.0
scipy>=1.10.0  # For A/B test statistical analysis
```

## Future Enhancements

- [ ] CLIP embedding generation from video frames
- [ ] Transformer-based sequential modeling
- [ ] Multi-task learning for multiple objectives
- [ ] Online learning / continual training
- [ ] Federated learning for privacy
- [ ] Explainability (attention weights, feature importance)
- [ ] Cold start handling for new users/videos

## License

Part of ClipStream2 - TikTok-style video platform
