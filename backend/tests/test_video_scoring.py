"""

Video Scoring Model Test Suite

 

Tests the AI-based video scoring and recommendation system:

- Feature extraction

- Model inference

- Ranking quality

- Event recording

- Feed personalization

"""

 

import asyncio

import sys

import os

from pathlib import Path

from typing import List, Dict

import logging

import numpy as np

 

# Add backend to path

backend_path = Path(__file__).parent.parent

sys.path.insert(0, str(backend_path))

 

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

 

 

class VideoScoringTester:

    """Comprehensive tests for video scoring system."""

 

    def __init__(self):

        """Initialize tester."""

        self.test_results = {

            'passed': 0,

            'failed': 0,

            'errors': []

        }

 

    def test_feature_extraction(self):

        """Test feature extraction from videos and users."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Feature Extraction")

        logger.info("="*50)

 

        try:

            from ml.features import VideoFeatureExtractor

 

            extractor = VideoFeatureExtractor()

 

            # Test video data

            video_data = {

                'id': 'video:test1',

                'title': 'Test Video',

                'duration': 60,

                'view_count': 1000,

                'like_count': 100,

                'comment_count': 50,

                'share_count': 20,

                'hashtags': ['test', 'viral'],

                'created_at': '2024-01-01T12:00:00Z',

                'clip_embedding': list(np.random.randn(512).astype(float))

            }

 

            # Test user data

            user_data = {

                'id': 'user:test1',

                'active_hours': [12, 13, 14, 15]

            }

 

            # Extract features

            clip_emb, inter_feat, user_feat = extractor.extract_all_features(

                video_data=video_data,

                user_data=user_data,

                user_history=[]

            )

 

            # Validate shapes

            assert clip_emb.shape == (512,), f"CLIP embedding shape mismatch: {clip_emb.shape}"

            assert inter_feat.shape == (8,), f"Interaction features shape mismatch: {inter_feat.shape}"

            assert user_feat.shape == (6,), f"User features shape mismatch: {user_feat.shape}"

 

            # Validate ranges

            assert all(0 <= x <= 1 for x in inter_feat), "Interaction features out of range"

            assert all(0 <= x <= 1 for x in user_feat), "User features out of range"

 

            logger.info("✅ Feature extraction test PASSED")

            logger.info(f"   CLIP embedding: {clip_emb.shape}")

            logger.info(f"   Interaction features: {inter_feat.shape}")

            logger.info(f"   User features: {user_feat.shape}")

 

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Feature extraction test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def test_model_inference(self):

        """Test model scoring and inference."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Model Inference")

        logger.info("="*50)

 

        try:

            from ml.models import VideoScoringModel

            from ml.config import get_config

            import torch

 

            # Create model with engagement config

            config = get_config('engagement')

            model = VideoScoringModel(weight_config=config.to_dict())

            model.eval()

 

            # Create dummy inputs

            batch_size = 5

            clip_emb = torch.randn(batch_size, 512)

            inter_feat = torch.rand(batch_size, 8)

            user_feat = torch.rand(batch_size, 6)

 

            # Forward pass

            with torch.no_grad():

                scores = model(clip_emb, inter_feat, user_feat)

 

            # Validate output

            assert scores.shape == (batch_size, 1), f"Output shape mismatch: {scores.shape}"

            assert not torch.isnan(scores).any(), "NaN values in scores"

            assert not torch.isinf(scores).any(), "Inf values in scores"

 

            # Check tower weights

            tower_weights = model.get_tower_weights()

            assert abs(sum(tower_weights.values()) - 1.0) < 0.01, "Tower weights don't sum to 1"

 

            logger.info("✅ Model inference test PASSED")

            logger.info(f"   Batch size: {batch_size}")

            logger.info(f"   Output shape: {scores.shape}")

            logger.info(f"   Score range: [{scores.min().item():.3f}, {scores.max().item():.3f}]")

            logger.info(f"   Tower weights: {tower_weights}")

 

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Model inference test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def test_multi_objective_model(self):

        """Test multi-objective scoring model."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Multi-Objective Model")

        logger.info("="*50)

 

        try:

            from ml.models import MultiObjectiveVideoScorer

            import torch

 

            model = MultiObjectiveVideoScorer()

            model.eval()

 

            # Create dummy inputs

            batch_size = 3

            clip_emb = torch.randn(batch_size, 512)

            inter_feat = torch.rand(batch_size, 8)

            user_feat = torch.rand(batch_size, 6)

 

            # Test each objective

            objectives = ['engagement', 'retention', 'discovery', 'monetization']

 

            with torch.no_grad():

                for objective in objectives:

                    scores = model(clip_emb, inter_feat, user_feat, objective=objective)

 

                    assert scores.shape == (batch_size, 1), f"Shape mismatch for {objective}"

                    assert not torch.isnan(scores).any(), f"NaN in {objective} scores"

 

                    logger.info(f"   {objective:15s}: {scores.mean().item():.3f} ± {scores.std().item():.3f}")

 

                # Test combined scoring

                combined = model(clip_emb, inter_feat, user_feat, objective=None)

                assert combined.shape == (batch_size, 1), "Combined shape mismatch"

 

                # Test get_all_scores

                all_scores = model.get_all_scores(clip_emb, inter_feat, user_feat)

                assert len(all_scores) == 4, "Should return 4 objectives"

 

            logger.info("✅ Multi-objective model test PASSED")

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Multi-objective model test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def test_model_configs(self):

        """Test model configuration presets."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Model Configurations")

        logger.info("="*50)

 

        try:

            from ml.config import (

                get_config,

                list_objectives,

                create_custom_config,

                ENGAGEMENT_CONFIG,

                RETENTION_CONFIG,

                VIRAL_CONFIG

            )

 

            # Test all objectives

            objectives = list_objectives()

            assert len(objectives) == 6, f"Expected 6 objectives, got {len(objectives)}"

 

            logger.info(f"   Available objectives: {', '.join(objectives)}")

 

            for obj in objectives:

                config = get_config(obj)

 

                # Validate weights sum close to 1

                weight_sum = (

                    config.content_weight +

                    config.interaction_weight +

                    config.user_weight

                )

                assert abs(weight_sum - 1.0) < 0.01, f"{obj}: Weights don't sum to 1"

 

                logger.info(

                    f"   {obj:12s}: content={config.content_weight:.2f}, "

                    f"interaction={config.interaction_weight:.2f}, "

                    f"user={config.user_weight:.2f}, "

                    f"freshness_decay={config.freshness_decay:.0f}h"

                )

 

            # Test custom config

            custom = create_custom_config(

                content_weight=0.5,

                interaction_weight=0.3,

                user_weight=0.2

            )

            assert custom.content_weight == 0.5, "Custom config failed"

 

            logger.info("✅ Model configurations test PASSED")

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Model configurations test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def test_ranking_metrics(self):

        """Test ranking evaluation metrics."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Ranking Metrics")

        logger.info("="*50)

 

        try:

            from ml.evaluation import RankingMetrics

 

            metrics = RankingMetrics()

 

            # Test data: relevance scores in ranked order

            relevance_scores = [1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0]

 

            # Test NDCG@K

            ndcg_10 = metrics.ndcg_at_k(relevance_scores, k=10)

            assert 0 <= ndcg_10 <= 1, f"NDCG out of range: {ndcg_10}"

 

            # Test MRR

            mrr = metrics.mrr(relevance_scores, threshold=0.5)

            assert 0 <= mrr <= 1, f"MRR out of range: {mrr}"

 

            # Test Precision@K

            precision_5 = metrics.precision_at_k(relevance_scores, k=5, threshold=0.5)

            assert 0 <= precision_5 <= 1, f"Precision out of range: {precision_5}"

 

            # Test Recall@K

            recall_5 = metrics.recall_at_k(relevance_scores, k=5, threshold=0.5)

            assert 0 <= recall_5 <= 1, f"Recall out of range: {recall_5}"

 

            logger.info("✅ Ranking metrics test PASSED")

            logger.info(f"   NDCG@10:      {ndcg_10:.3f}")

            logger.info(f"   MRR:          {mrr:.3f}")

            logger.info(f"   Precision@5:  {precision_5:.3f}")

            logger.info(f"   Recall@5:     {recall_5:.3f}")

 

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Ranking metrics test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def test_engagement_metrics(self):

        """Test engagement evaluation metrics."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Engagement Metrics")

        logger.info("="*50)

 

        try:

            from ml.evaluation import EngagementMetrics

 

            metrics = EngagementMetrics()

 

            # Test CTR

            ctr = metrics.click_through_rate(impressions=1000, clicks=150)

            assert ctr == 0.15, f"CTR calculation wrong: {ctr}"

 

            # Test engagement rate

            eng_rate = metrics.engagement_rate(

                views=1000,

                likes=100,

                comments=50,

                shares=20

            )

            assert eng_rate == 0.17, f"Engagement rate wrong: {eng_rate}"

 

            # Test completion rate

            completion = metrics.completion_rate(

                total_views=1000,

                completed_views=600

            )

            assert completion == 0.6, f"Completion rate wrong: {completion}"

 

            # Test watch time ratio

            watch_ratio = metrics.average_watch_time_ratio(

                watch_times=[30, 45, 60],

                durations=[60, 60, 60]

            )

            assert 0 <= watch_ratio <= 1, f"Watch ratio out of range: {watch_ratio}"

 

            logger.info("✅ Engagement metrics test PASSED")

            logger.info(f"   CTR:              {ctr:.2%}")

            logger.info(f"   Engagement rate:  {eng_rate:.2%}")

            logger.info(f"   Completion rate:  {completion:.2%}")

            logger.info(f"   Watch time ratio: {watch_ratio:.2%}")

 

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Engagement metrics test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def test_batch_feature_extraction(self):

        """Test batch feature extraction for efficiency."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Batch Feature Extraction")

        logger.info("="*50)

 

        try:

            from ml.features import BatchFeatureExtractor

            import time

 

            extractor = BatchFeatureExtractor()

 

            # Create batch of test videos

            batch_size = 50

            videos = []

            for i in range(batch_size):

                videos.append({

                    'id': f'video:test{i}',

                    'title': f'Test Video {i}',

                    'duration': 60,

                    'view_count': 1000 + i * 100,

                    'like_count': 100 + i * 10,

                    'comment_count': 50 + i * 5,

                    'share_count': 20 + i * 2,

                    'hashtags': ['test'],

                    'created_at': '2024-01-01T12:00:00Z'

                })

 

            user_data = {'id': 'user:test1', 'active_hours': [12]}

 

            # Extract batch

            start_time = time.time()

            clip_emb, inter_feat, user_feat = extractor.extract_batch(

                videos=videos,

                user_data=user_data

            )

            elapsed = time.time() - start_time

 

            # Validate shapes

            assert clip_emb.shape == (batch_size, 512), f"CLIP batch shape: {clip_emb.shape}"

            assert inter_feat.shape == (batch_size, 8), f"Interaction batch shape: {inter_feat.shape}"

            assert user_feat.shape == (batch_size, 6), f"User batch shape: {user_feat.shape}"

 

            logger.info("✅ Batch feature extraction test PASSED")

            logger.info(f"   Batch size: {batch_size}")

            logger.info(f"   Processing time: {elapsed*1000:.1f}ms ({elapsed*1000/batch_size:.2f}ms per video)")

            logger.info(f"   Throughput: {batch_size/elapsed:.1f} videos/sec")

 

            self.test_results['passed'] += 1

 

        except Exception as e:

            logger.error(f"❌ Batch feature extraction test FAILED: {e}")

            self.test_results['failed'] += 1

            self.test_results['errors'].append(str(e))

 

    def run_all_tests(self):

        """Run all tests and print summary."""

        logger.info("\n" + "="*70)

        logger.info("RUNNING VIDEO SCORING TEST SUITE")

        logger.info("="*70)

 

        # Run tests

        self.test_feature_extraction()

        self.test_model_inference()

        self.test_multi_objective_model()

        self.test_model_configs()

        self.test_ranking_metrics()

        self.test_engagement_metrics()

        self.test_batch_feature_extraction()

 

        # Print summary

        logger.info("\n" + "="*70)

        logger.info("TEST SUMMARY")

        logger.info("="*70)

        logger.info(f"✅ Passed: {self.test_results['passed']}")

        logger.info(f"❌ Failed: {self.test_results['failed']}")

 

        if self.test_results['errors']:

            logger.info("\nErrors:")

            for i, error in enumerate(self.test_results['errors'], 1):

                logger.info(f"  {i}. {error}")

 

        total = self.test_results['passed'] + self.test_results['failed']

        success_rate = (self.test_results['passed'] / total * 100) if total > 0 else 0

 

        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")

 

        return self.test_results['failed'] == 0

 

 

def main():

    """Main test runner."""

    tester = VideoScoringTester()

    success = tester.run_all_tests()

 

    if success:

        logger.info("\n🎉 All tests passed!")

        sys.exit(0)

    else:

        logger.error("\n💥 Some tests failed!")

        sys.exit(1)

 

 

if __name__ == "__main__":

    main()