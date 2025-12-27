"""

Integration Tests for Video Scoring and Feed API

 

Tests the full pipeline:

1. Video ingestion

2. User interaction events

3. AI scoring and ranking

4. Feed personalization

5. Virality detection

"""

 

import asyncio

import httpx

from typing import List, Dict

import logging

import sys

from pathlib import Path

import random

 

# Add backend to path

backend_path = Path(__file__).parent.parent

sys.path.insert(0, str(backend_path))

 

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

 

 

class IntegrationTester:

    """End-to-end integration tests."""

 

    def __init__(self, backend_url: str = "http://localhost:8080"):

        """

        Initialize integration tester.

 

        Args:

            backend_url: Backend API URL

        """

        self.backend_url = backend_url.rstrip('/')

        self.client = httpx.AsyncClient(timeout=30.0)

        self.test_user_id = None

        self.test_videos = []

 

    async def setup_test_data(self, num_videos: int = 10):

        """

        Set up test data: videos and user.

 

        Args:

            num_videos: Number of test videos to create

        """

        logger.info("\n" + "="*50)

        logger.info("SETUP: Creating Test Data")

        logger.info("="*50)

 

        # Create test videos using the seed endpoint

        logger.info(f"Creating {num_videos} test videos...")

 

        for i in range(num_videos):

            try:

                response = await self.client.post(

                    f"{self.backend_url}/api/v1/feed/debug/seed-video",

                    json={

                        "title": f"Test Video {i+1}",

                        "force": True

                    }

                )

 

                if response.status_code == 200:

                    result = response.json()

                    video = result.get("video", {})

                    video_id = video.get("id")

 

                    if video_id:

                        self.test_videos.append(video)

                        logger.info(f"  ✅ Created video: {video_id}")

 

                        # Extract user_id from first video

                        if not self.test_user_id:

                            self.test_user_id = video.get("user_id")

 

                await asyncio.sleep(0.2)  # Small delay

 

            except Exception as e:

                logger.error(f"  ❌ Failed to create video {i+1}: {e}")

 

        logger.info(f"\n✅ Test data setup complete:")

        logger.info(f"   Videos created: {len(self.test_videos)}")

        logger.info(f"   Test user ID: {self.test_user_id}")

 

    async def test_feed_endpoints(self):

        """Test feed API endpoints."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Feed API Endpoints")

        logger.info("="*50)

 

        tests_passed = 0

        tests_failed = 0

 

        # Test 1: For You feed (no AI)

        try:

            logger.info("\n1. Testing For You feed (no AI)...")

            response = await self.client.get(

                f"{self.backend_url}/api/v1/feed/for-you",

                params={"limit": 10, "use_ai": False}

            )

 

            assert response.status_code == 200, f"Status code: {response.status_code}"

            data = response.json()

            assert isinstance(data, list), "Response should be a list"

            logger.info(f"   ✅ Received {len(data)} videos")

            tests_passed += 1

 

        except Exception as e:

            logger.error(f"   ❌ Test failed: {e}")

            tests_failed += 1

 

        # Test 2: For You feed (with AI, if available)

        try:

            logger.info("\n2. Testing For You feed (with AI)...")

            response = await self.client.get(

                f"{self.backend_url}/api/v1/feed/for-you",

                params={

                    "limit": 10,

                    "use_ai": True,

                    "user_id": self.test_user_id or "user:test"

                }

            )

 

            assert response.status_code == 200, f"Status code: {response.status_code}"

            data = response.json()

            assert isinstance(data, list), "Response should be a list"

            logger.info(f"   ✅ Received {len(data)} videos (AI ranking attempted)")

            tests_passed += 1

 

        except Exception as e:

            logger.error(f"   ❌ Test failed: {e}")

            tests_failed += 1

 

        # Test 3: Trending feed

        try:

            logger.info("\n3. Testing Trending feed...")

            response = await self.client.get(

                f"{self.backend_url}/api/v1/feed/trending",

                params={"limit": 10}

            )

 

            assert response.status_code == 200, f"Status code: {response.status_code}"

            data = response.json()

            assert isinstance(data, list), "Response should be a list"

            logger.info(f"   ✅ Received {len(data)} videos")

            tests_passed += 1

 

        except Exception as e:

            logger.error(f"   ❌ Test failed: {e}")

            tests_failed += 1

 

        # Test 4: Recent videos debug endpoint

        try:

            logger.info("\n4. Testing debug/recent-videos endpoint...")

            response = await self.client.get(

                f"{self.backend_url}/api/v1/feed/debug/recent-videos",

                params={"limit": 5}

            )

 

            assert response.status_code == 200, f"Status code: {response.status_code}"

            data = response.json()

            assert "videos" in data, "Response should have 'videos' field"

            logger.info(f"   ✅ Received {len(data['videos'])} videos")

            tests_passed += 1

 

        except Exception as e:

            logger.error(f"   ❌ Test failed: {e}")

            tests_failed += 1

 

        logger.info(f"\n📊 Feed API Tests: {tests_passed}/{tests_passed + tests_failed} passed")

        return tests_failed == 0

 

    async def test_event_recording(self):

        """Test video event recording."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Video Event Recording")

        logger.info("="*50)

 

        if not self.test_videos:

            logger.warning("⚠️  No test videos available, skipping event recording test")

            return False

 

        try:

            from ml.events import VideoEventRecorder, EventType

            from db.surrealdb_client import db_client

 

            event_recorder = VideoEventRecorder(db_client)

 

            # Test video and user

            test_video = self.test_videos[0]

            video_id = test_video.get("id")

            user_id = self.test_user_id or "user:test"

 

            logger.info(f"\nRecording events for video {video_id}...")

 

            # 1. Record view

            view_event = await event_recorder.record_view(

                video_id=video_id,

                user_id=user_id,

                source="for_you"

            )

            logger.info("  ✅ View event recorded")

 

            # 2. Record watch

            watch_event = await event_recorder.record_watch(

                video_id=video_id,

                user_id=user_id,

                watch_time=45.0,

                video_duration=60.0,

                source="for_you"

            )

            logger.info("  ✅ Watch event recorded (45s / 60s)")

 

            # 3. Record like

            like_event = await event_recorder.record_engagement(

                event_type=EventType.LIKE,

                video_id=video_id,

                user_id=user_id

            )

            logger.info("  ✅ Like event recorded")

 

            # 4. Record comment

            comment_event = await event_recorder.record_engagement(

                event_type=EventType.COMMENT,

                video_id=video_id,

                user_id=user_id,

                metadata={"text": "Great video!"}

            )

            logger.info("  ✅ Comment event recorded")

 

            # 5. Record skip (for another video)

            if len(self.test_videos) > 1:

                skip_video_id = self.test_videos[1].get("id")

                skip_event = await event_recorder.record_skip(

                    video_id=skip_video_id,

                    user_id=user_id,

                    watch_time=2.0,

                    video_duration=60.0,

                    reason="not_interested"

                )

                logger.info("  ✅ Skip event recorded")

 

            # 6. Get user events

            user_events = await event_recorder.get_user_events(

                user_id=user_id,

                limit=10

            )

            logger.info(f"  ✅ Retrieved {len(user_events)} user events")

 

            # 7. Compute virality metrics

            virality = await event_recorder.compute_virality_metrics(video_id)

            logger.info(f"  ✅ Virality metrics: velocity={virality.get('velocity', 0):.2f} views/hour")

 

            logger.info("\n✅ Event recording test PASSED")

            return True

 

        except Exception as e:

            logger.error(f"❌ Event recording test FAILED: {e}")

            import traceback

            traceback.print_exc()

            return False

 

    async def test_ai_scoring_integration(self):

        """Test AI scoring integration with feed."""

        logger.info("\n" + "="*50)

        logger.info("TEST: AI Scoring Integration")

        logger.info("="*50)

 

        try:

            from ml.inference import VideoScorerService

            from ml.config import get_config

 

            # Initialize scoring service

            scorer = VideoScorerService(

                model_path=None,  # Use untrained model for testing

                device='cpu'

            )

 

            logger.info("  ✅ Scoring service initialized")

 

            # Create mock video and user data

            videos = [

                {

                    'id': f'video:test{i}',

                    'title': f'Test Video {i}',

                    'duration': 60,

                    'view_count': 1000 + i * 100,

                    'like_count': 100 + i * 10,

                    'comment_count': 50,

                    'share_count': 20,

                    'hashtags': ['test'],

                    'created_at': '2024-01-01T12:00:00Z'

                }

                for i in range(10)

            ]

 

            user_data = {

                'id': 'user:test1',

                'active_hours': [12, 13, 14]

            }

 

            # Score videos

            scored_videos = await scorer.score_videos(

                videos=videos,

                user_data=user_data,

                user_history=None,

                objective='engagement'

            )

 

            logger.info(f"  ✅ Scored {len(scored_videos)} videos")

 

            # Verify scores

            assert len(scored_videos) == len(videos), "Score count mismatch"

            assert all(isinstance(score, float) for _, score in scored_videos), "Invalid scores"

 

            # Check if scores are sorted descending

            scores = [score for _, score in scored_videos]

            assert scores == sorted(scores, reverse=True), "Scores not sorted"

 

            logger.info(f"  ✅ Score range: [{min(scores):.3f}, {max(scores):.3f}]")

 

            # Test model info

            info = scorer.get_model_info()

            logger.info(f"  ✅ Model info: {info}")

 

            logger.info("\n✅ AI scoring integration test PASSED")

            return True

 

        except Exception as e:

            logger.error(f"❌ AI scoring integration test FAILED: {e}")

            import traceback

            traceback.print_exc()

            return False

 

    async def test_virality_detection(self):

        """Test virality detection system."""

        logger.info("\n" + "="*50)

        logger.info("TEST: Virality Detection")

        logger.info("="*50)

 

        if not self.test_videos:

            logger.warning("⚠️  No test videos available, skipping virality test")

            return False

 

        try:

            from ml.events import VideoEventRecorder, EventType

            from db.surrealdb_client import db_client

 

            event_recorder = VideoEventRecorder(db_client)

 

            # Simulate viral video by creating many events

            viral_video_id = self.test_videos[0].get("id")

            user_id = self.test_user_id or "user:test"

 

            logger.info(f"\nSimulating viral activity for {viral_video_id}...")

 

            # Record multiple views and engagements

            for i in range(20):

                test_user = f"{user_id}_{i}"

 

                # View

                await event_recorder.record_view(

                    video_id=viral_video_id,

                    user_id=test_user,

                    source="for_you"

                )

 

                # Some watch

                if i % 2 == 0:

                    await event_recorder.record_watch(

                        video_id=viral_video_id,

                        user_id=test_user,

                        watch_time=50.0,

                        video_duration=60.0

                    )

 

                # Some like

                if i % 3 == 0:

                    await event_recorder.record_engagement(

                        event_type=EventType.LIKE,

                        video_id=viral_video_id,

                        user_id=test_user

                    )

 

                # Some share

                if i % 5 == 0:

                    await event_recorder.record_engagement(

                        event_type=EventType.SHARE,

                        video_id=viral_video_id,

                        user_id=test_user

                    )

 

            logger.info("  ✅ Simulated 20 user interactions")

 

            # Compute virality metrics

            virality = await event_recorder.compute_virality_metrics(viral_video_id)

 

            logger.info(f"\nVirality Metrics:")

            logger.info(f"  Is Viral: {virality.get('is_viral')}")

            logger.info(f"  Is Trending: {virality.get('is_trending')}")

            logger.info(f"  Velocity: {virality.get('velocity', 0):.2f} views/hour")

            logger.info(f"  Engagement Rate: {virality.get('engagement_rate', 0):.2%}")

            logger.info(f"  Total Views (24h): {virality.get('total_views_24h', 0)}")

            logger.info(f"  Total Engagements (24h): {virality.get('total_engagements_24h', 0)}")

 

            logger.info("\n✅ Virality detection test PASSED")

            return True

 

        except Exception as e:

            logger.error(f"❌ Virality detection test FAILED: {e}")

            import traceback

            traceback.print_exc()

            return False

 

    async def cleanup(self):

        """Clean up test resources."""

        await self.client.aclose()

 

    async def run_all_tests(self):

        """Run all integration tests."""

        logger.info("\n" + "="*70)

        logger.info("RUNNING INTEGRATION TEST SUITE")

        logger.info("="*70)

 

        results = {

            'passed': 0,

            'failed': 0

        }

 

        # Setup test data

        await self.setup_test_data(num_videos=5)

 

        # Run tests

        tests = [

            ("Feed API Endpoints", self.test_feed_endpoints),

            ("Event Recording", self.test_event_recording),

            ("AI Scoring Integration", self.test_ai_scoring_integration),

            ("Virality Detection", self.test_virality_detection)

        ]

 

        for test_name, test_func in tests:

            try:

                success = await test_func()

                if success:

                    results['passed'] += 1

                else:

                    results['failed'] += 1

            except Exception as e:

                logger.error(f"❌ {test_name} crashed: {e}")

                results['failed'] += 1

 

        # Print summary

        logger.info("\n" + "="*70)

        logger.info("INTEGRATION TEST SUMMARY")

        logger.info("="*70)

        logger.info(f"✅ Passed: {results['passed']}")

        logger.info(f"❌ Failed: {results['failed']}")

 

        total = results['passed'] + results['failed']

        success_rate = (results['passed'] / total * 100) if total > 0 else 0

        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")

 

        return results['failed'] == 0

 

 

async def main():

    """Main test runner."""

    tester = IntegrationTester()

 

    try:

        success = await tester.run_all_tests()

 

        if success:

            logger.info("\n🎉 All integration tests passed!")

            return 0

        else:

            logger.error("\n💥 Some integration tests failed!")

            return 1

 

    finally:

        await tester.cleanup()

 

 

if __name__ == "__main__":

    exit_code = asyncio.run(main())

    sys.exit(exit_code)
