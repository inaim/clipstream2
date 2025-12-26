# 🤖 ML Ranking Algorithm

TikTok-style 3-component scoring algorithm.

## Components

1. **User Interest (60%)**
   - Category preferences
   - Embedding similarity
   - Watch history

2. **Video Quality (30%)**
   - Engagement metrics
   - Age decay
   - Laplace smoothing

3. **Exploration (10%)**
   - UCB discovery bonus
   - Unseen content boost

## Formula

```python
final_score = (
    0.6 * user_interest_score +
    0.3 * video_quality_score +
    0.1 * exploration_bonus
)
```

## Diversity Re-ranking

Prevents category clustering by penalizing consecutive videos from same category.

See full details in backend/app/scoring.py
