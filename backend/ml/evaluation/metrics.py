"""
Evaluation Metrics and Monitoring for Video Scoring Model

Provides tools to evaluate model performance and monitor production metrics:
- Ranking metrics (NDCG, MRR, Precision@K)
- Engagement metrics (CTR, watch time, completion rate)
- A/B test analysis
- Real-time monitoring dashboards
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RankingMetrics:
    """Metrics for evaluating ranking quality."""

    @staticmethod
    def ndcg_at_k(relevance_scores: List[float], k: int = 10) -> float:
        """
        Normalized Discounted Cumulative Gain at K.

        Measures ranking quality with position-based discounting.

        Args:
            relevance_scores: List of relevance scores in ranked order
            k: Cutoff position

        Returns:
            ndcg: NDCG@K score [0, 1]
        """
        def dcg(scores: List[float]) -> float:
            return sum(
                (2**score - 1) / np.log2(idx + 2)
                for idx, score in enumerate(scores)
            )

        # Get DCG of top k
        actual_dcg = dcg(relevance_scores[:k])

        # Get ideal DCG (best possible ranking)
        ideal_scores = sorted(relevance_scores, reverse=True)
        ideal_dcg = dcg(ideal_scores[:k])

        # Normalize
        if ideal_dcg == 0:
            return 0.0

        return actual_dcg / ideal_dcg

    @staticmethod
    def mrr(relevance_scores: List[float], threshold: float = 0.5) -> float:
        """
        Mean Reciprocal Rank.

        Finds the position of the first relevant item.

        Args:
            relevance_scores: List of relevance scores in ranked order
            threshold: Score threshold for relevance

        Returns:
            mrr: MRR score
        """
        for idx, score in enumerate(relevance_scores):
            if score >= threshold:
                return 1.0 / (idx + 1)

        return 0.0

    @staticmethod
    def precision_at_k(relevance_scores: List[float], k: int = 10, threshold: float = 0.5) -> float:
        """
        Precision at K.

        Fraction of top K items that are relevant.

        Args:
            relevance_scores: List of relevance scores in ranked order
            k: Cutoff position
            threshold: Score threshold for relevance

        Returns:
            precision: Precision@K [0, 1]
        """
        if k == 0:
            return 0.0

        relevant_count = sum(
            1 for score in relevance_scores[:k]
            if score >= threshold
        )

        return relevant_count / k

    @staticmethod
    def recall_at_k(relevance_scores: List[float], k: int = 10, threshold: float = 0.5) -> float:
        """
        Recall at K.

        Fraction of relevant items found in top K.

        Args:
            relevance_scores: List of relevance scores in ranked order
            k: Cutoff position
            threshold: Score threshold for relevance

        Returns:
            recall: Recall@K [0, 1]
        """
        total_relevant = sum(
            1 for score in relevance_scores
            if score >= threshold
        )

        if total_relevant == 0:
            return 0.0

        relevant_in_k = sum(
            1 for score in relevance_scores[:k]
            if score >= threshold
        )

        return relevant_in_k / total_relevant


class EngagementMetrics:
    """Metrics for measuring user engagement."""

    @staticmethod
    def click_through_rate(impressions: int, clicks: int) -> float:
        """
        Calculate CTR.

        Args:
            impressions: Number of times shown
            clicks: Number of times clicked/viewed

        Returns:
            ctr: Click-through rate [0, 1]
        """
        if impressions == 0:
            return 0.0

        return clicks / impressions

    @staticmethod
    def engagement_rate(
        views: int,
        likes: int,
        comments: int,
        shares: int
    ) -> float:
        """
        Calculate overall engagement rate.

        Args:
            views: Number of views
            likes: Number of likes
            comments: Number of comments
            shares: Number of shares

        Returns:
            rate: Engagement rate [0, 1]
        """
        if views == 0:
            return 0.0

        total_engagements = likes + comments + shares
        return total_engagements / views

    @staticmethod
    def completion_rate(
        total_views: int,
        completed_views: int
    ) -> float:
        """
        Calculate video completion rate.

        Args:
            total_views: Total number of views
            completed_views: Number of views that watched to completion

        Returns:
            rate: Completion rate [0, 1]
        """
        if total_views == 0:
            return 0.0

        return completed_views / total_views

    @staticmethod
    def average_watch_time_ratio(watch_times: List[float], durations: List[float]) -> float:
        """
        Calculate average watch time as fraction of video duration.

        Args:
            watch_times: List of watch times in seconds
            durations: List of video durations in seconds

        Returns:
            ratio: Average watch time ratio [0, 1]
        """
        if not watch_times or not durations:
            return 0.0

        ratios = [
            min(1.0, wt / dur) if dur > 0 else 0.0
            for wt, dur in zip(watch_times, durations)
        ]

        return np.mean(ratios)


class ModelEvaluator:
    """
    Evaluates trained model performance on test data.
    """

    def __init__(self, model_service):
        """
        Initialize evaluator.

        Args:
            model_service: VideoScorerService instance
        """
        self.model_service = model_service
        self.ranking_metrics = RankingMetrics()
        self.engagement_metrics = EngagementMetrics()

    async def evaluate_ranking(
        self,
        test_data: List[Dict],
        k_values: List[int] = [5, 10, 20, 50]
    ) -> Dict[str, float]:
        """
        Evaluate model ranking performance.

        Args:
            test_data: List of test samples with videos, user data, and labels
            k_values: List of K values for precision@K, recall@K

        Returns:
            metrics: Dictionary of metric scores
        """
        ndcg_scores = []
        mrr_scores = []
        precision_scores = {k: [] for k in k_values}
        recall_scores = {k: [] for k in k_values}

        for sample in test_data:
            videos = sample['videos']
            user_data = sample['user']
            true_scores = sample['labels']  # Ground truth relevance

            # Get model predictions
            scored_videos = await self.model_service.score_videos(
                videos=videos,
                user_data=user_data,
                user_history=sample.get('history')
            )

            # Extract predicted order
            predicted_order = {vid_id: idx for idx, (vid_id, _) in enumerate(scored_videos)}

            # Reorder true scores by predicted ranking
            ranked_true_scores = []
            for vid in videos:
                vid_id = vid['id']
                true_idx = videos.index(vid)
                ranked_true_scores.append(true_scores[true_idx])

            # Calculate metrics
            ndcg_scores.append(self.ranking_metrics.ndcg_at_k(ranked_true_scores, k=10))
            mrr_scores.append(self.ranking_metrics.mrr(ranked_true_scores))

            for k in k_values:
                precision_scores[k].append(
                    self.ranking_metrics.precision_at_k(ranked_true_scores, k=k)
                )
                recall_scores[k].append(
                    self.ranking_metrics.recall_at_k(ranked_true_scores, k=k)
                )

        # Aggregate results
        results = {
            'ndcg@10': np.mean(ndcg_scores),
            'mrr': np.mean(mrr_scores)
        }

        for k in k_values:
            results[f'precision@{k}'] = np.mean(precision_scores[k])
            results[f'recall@{k}'] = np.mean(recall_scores[k])

        return results

    async def evaluate_engagement(
        self,
        predictions: List[Tuple[str, float]],
        actual_engagement: Dict[str, Dict]
    ) -> Dict[str, float]:
        """
        Evaluate how well model predictions correlate with actual engagement.

        Args:
            predictions: List of (video_id, predicted_score) tuples
            actual_engagement: Dict mapping video_id to actual engagement metrics

        Returns:
            metrics: Correlation scores and other engagement metrics
        """
        predicted_scores = []
        actual_scores = []

        for video_id, pred_score in predictions:
            if video_id in actual_engagement:
                eng = actual_engagement[video_id]

                # Calculate actual engagement score
                actual_score = self.engagement_metrics.engagement_rate(
                    views=eng.get('views', 0),
                    likes=eng.get('likes', 0),
                    comments=eng.get('comments', 0),
                    shares=eng.get('shares', 0)
                )

                predicted_scores.append(pred_score)
                actual_scores.append(actual_score)

        # Calculate correlation
        if len(predicted_scores) > 1:
            correlation = np.corrcoef(predicted_scores, actual_scores)[0, 1]
        else:
            correlation = 0.0

        return {
            'engagement_correlation': correlation,
            'num_samples': len(predicted_scores)
        }


class ProductionMonitor:
    """
    Monitors model performance in production.

    Tracks real-time metrics and detects performance degradation.
    """

    def __init__(self, db_client):
        """
        Initialize production monitor.

        Args:
            db_client: Database client for querying events
        """
        self.db = db_client
        self.engagement_metrics = EngagementMetrics()

    async def get_recent_metrics(
        self,
        hours: int = 24
    ) -> Dict[str, float]:
        """
        Get metrics from recent production traffic.

        Args:
            hours: Number of hours to look back

        Returns:
            metrics: Dictionary of production metrics
        """
        # Query recent events
        cutoff_time = datetime.now() - timedelta(hours=hours)

        query = f"""
            SELECT type, metadata FROM video_events
            WHERE timestamp > $cutoff
        """

        events = await self.db.query(query, {
            "cutoff": cutoff_time.isoformat()
        })

        if not events:
            return {}

        # Count event types
        views = sum(1 for e in events if e['type'] == 'view')
        watches = sum(1 for e in events if e['type'] == 'watch')
        completes = sum(1 for e in events if e['type'] == 'complete')
        likes = sum(1 for e in events if e['type'] == 'like')
        comments = sum(1 for e in events if e['type'] == 'comment')
        shares = sum(1 for e in events if e['type'] == 'share')
        skips = sum(1 for e in events if e['type'] == 'skip')

        # Calculate metrics
        metrics = {
            'total_events': len(events),
            'views': views,
            'watches': watches,
            'completes': completes,
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'skips': skips,
            'watch_rate': watches / views if views > 0 else 0.0,
            'completion_rate': completes / views if views > 0 else 0.0,
            'engagement_rate': (likes + comments + shares) / views if views > 0 else 0.0,
            'skip_rate': skips / views if views > 0 else 0.0
        }

        return metrics

    async def detect_anomalies(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        threshold: float = 0.2
    ) -> List[str]:
        """
        Detect anomalies by comparing current metrics to baseline.

        Args:
            current_metrics: Current production metrics
            baseline_metrics: Baseline/expected metrics
            threshold: Relative change threshold for anomaly (default 20%)

        Returns:
            anomalies: List of detected anomaly descriptions
        """
        anomalies = []

        for metric_name in ['watch_rate', 'completion_rate', 'engagement_rate', 'skip_rate']:
            if metric_name not in current_metrics or metric_name not in baseline_metrics:
                continue

            current = current_metrics[metric_name]
            baseline = baseline_metrics[metric_name]

            if baseline == 0:
                continue

            relative_change = abs(current - baseline) / baseline

            if relative_change > threshold:
                direction = "increased" if current > baseline else "decreased"
                anomalies.append(
                    f"{metric_name} {direction} by {relative_change*100:.1f}% "
                    f"(from {baseline:.3f} to {current:.3f})"
                )

        return anomalies


class ABTestAnalyzer:
    """Analyzes A/B test results for model variants."""

    @staticmethod
    def calculate_lift(
        control_metric: float,
        treatment_metric: float
    ) -> float:
        """
        Calculate percentage lift of treatment over control.

        Args:
            control_metric: Control group metric value
            treatment_metric: Treatment group metric value

        Returns:
            lift: Percentage lift (e.g., 0.15 = 15% improvement)
        """
        if control_metric == 0:
            return 0.0

        return (treatment_metric - control_metric) / control_metric

    @staticmethod
    def is_significant(
        control_samples: List[float],
        treatment_samples: List[float],
        alpha: float = 0.05
    ) -> Tuple[bool, float]:
        """
        Perform statistical significance test (t-test).

        Args:
            control_samples: Control group samples
            treatment_samples: Treatment group samples
            alpha: Significance level (default 0.05)

        Returns:
            is_sig: Whether difference is statistically significant
            p_value: P-value of the test
        """
        from scipy import stats

        t_stat, p_value = stats.ttest_ind(treatment_samples, control_samples)

        return p_value < alpha, p_value
