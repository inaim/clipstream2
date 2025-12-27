"""
Sample Data Generator for Testing

Generates realistic sample data for testing:
- Videos with varying popularity
- Users with different behaviors
- Interaction events (views, likes, comments, skips)
- Training datasets for model development
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generates realistic sample data for testing."""

    def __init__(self, seed: int = 42):
        """
        Initialize generator.

        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.video_count = 0
        self.user_count = 0
        self.event_count = 0

    def generate_users(self, count: int = 100) -> List[Dict]:
        """
        Generate sample user profiles.

        Args:
            count: Number of users to generate

        Returns:
            users: List of user dicts
        """
        logger.info(f"Generating {count} sample users...")

        users = []

        # User behavior archetypes
        archetypes = [
            {
                'name': 'casual_viewer',
                'avg_watch_time': 20,  # watches ~20s per video
                'interaction_rate': 0.05,  # interacts with 5% of videos
                'skip_rate': 0.4,  # skips 40% quickly
                'active_hours': list(range(18, 23)),  # evening viewer
            },
            {
                'name': 'engaged_user',
                'avg_watch_time': 45,
                'interaction_rate': 0.25,
                'skip_rate': 0.2,
                'active_hours': list(range(12, 20)),
            },
            {
                'name': 'power_user',
                'avg_watch_time': 55,
                'interaction_rate': 0.5,
                'skip_rate': 0.1,
                'active_hours': list(range(8, 24)),
            },
            {
                'name': 'selective_viewer',
                'avg_watch_time': 50,
                'interaction_rate': 0.15,
                'skip_rate': 0.6,  # very selective, skips a lot
                'active_hours': list(range(20, 24)),
            },
            {
                'name': 'binge_watcher',
                'avg_watch_time': 40,
                'interaction_rate': 0.1,
                'skip_rate': 0.3,
                'active_hours': list(range(0, 24)),  # all day
            }
        ]

        for i in range(count):
            archetype = random.choice(archetypes)

            user = {
                'id': f'user:sample_{self.user_count}',
                'username': f'user{self.user_count}',
                'archetype': archetype['name'],
                'avg_watch_time': archetype['avg_watch_time'] + random.randint(-10, 10),
                'interaction_rate': max(0, min(1, archetype['interaction_rate'] + random.uniform(-0.1, 0.1))),
                'skip_rate': max(0, min(1, archetype['skip_rate'] + random.uniform(-0.1, 0.1))),
                'active_hours': archetype['active_hours'],
                'favorite_categories': random.sample(
                    ['dance', 'comedy', 'cooking', 'fitness', 'tech', 'travel', 'pets', 'music', 'art', 'gaming'],
                    k=random.randint(2, 4)
                ),
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            }

            users.append(user)
            self.user_count += 1

        logger.info(f"Generated {len(users)} users with different behavior profiles")
        return users

    def generate_videos(self, count: int = 500) -> List[Dict]:
        """
        Generate sample videos with varying popularity.

        Args:
            count: Number of videos to generate

        Returns:
            videos: List of video dicts
        """
        logger.info(f"Generating {count} sample videos...")

        videos = []

        categories = ['dance', 'comedy', 'cooking', 'fitness', 'tech', 'travel', 'pets', 'music', 'art', 'gaming']

        # Popularity distribution (most videos are low engagement)
        popularity_tiers = [
            {'name': 'low', 'weight': 60, 'view_range': (100, 1000), 'engagement': 0.08},
            {'name': 'medium', 'weight': 25, 'view_range': (1000, 10000), 'engagement': 0.15},
            {'name': 'high', 'weight': 10, 'view_range': (10000, 100000), 'engagement': 0.22},
            {'name': 'viral', 'weight': 5, 'view_range': (100000, 1000000), 'engagement': 0.30}
        ]

        for i in range(count):
            # Select popularity tier
            tier = random.choices(
                popularity_tiers,
                weights=[t['weight'] for t in popularity_tiers]
            )[0]

            # Generate metrics
            view_count = random.randint(*tier['view_range'])
            base_engagement = tier['engagement']

            like_count = int(view_count * base_engagement * random.uniform(0.8, 1.2))
            comment_count = int(view_count * base_engagement * 0.4 * random.uniform(0.7, 1.3))
            share_count = int(view_count * base_engagement * 0.2 * random.uniform(0.6, 1.4))

            # Video metadata
            category = random.choice(categories)
            hashtags = [category, 'fyp']

            if random.random() < 0.3:
                hashtags.append('trending')
            if random.random() < 0.2:
                hashtags.append('viral')

            duration = random.choice([15, 30, 45, 60])

            # Age distribution (more recent = fewer old videos)
            days_ago = int(random.expovariate(1/15))  # exponential distribution, mean 15 days
            days_ago = min(days_ago, 90)  # cap at 90 days

            created_at = datetime.now() - timedelta(days=days_ago)

            video = {
                'id': f'video:sample_{self.video_count}',
                'title': f'{category.capitalize()} Video #{self.video_count}',
                'description': f'Sample {category} video for testing',
                'category': category,
                'hashtags': hashtags,
                'duration': duration,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'share_count': share_count,
                'popularity_tier': tier['name'],
                'created_at': created_at.isoformat(),
                'user_id': f'user:creator_{random.randint(0, 49)}'  # 50 creators
            }

            videos.append(video)
            self.video_count += 1

        logger.info(f"Generated {len(videos)} videos across popularity tiers:")
        for tier in popularity_tiers:
            tier_count = sum(1 for v in videos if v['popularity_tier'] == tier['name'])
            logger.info(f"  {tier['name']:8s}: {tier_count:4d} videos ({tier_count/len(videos)*100:.1f}%)")

        return videos

    def generate_interactions(
        self,
        users: List[Dict],
        videos: List[Dict],
        interactions_per_user: int = 50
    ) -> List[Dict]:
        """
        Generate realistic user-video interactions.

        Args:
            users: List of user dicts
            videos: List of video dicts
            interactions_per_user: Average interactions per user

        Returns:
            interactions: List of interaction events
        """
        logger.info(f"Generating interactions ({interactions_per_user} per user)...")

        interactions = []

        for user in users:
            num_interactions = int(interactions_per_user * random.uniform(0.5, 1.5))

            # User preferences affect which videos they see
            favorite_categories = user.get('favorite_categories', [])

            # Sample videos (biased towards user's favorite categories)
            candidate_videos = []
            for video in videos:
                if video['category'] in favorite_categories:
                    candidate_videos.extend([video] * 3)  # 3x weight
                else:
                    candidate_videos.append(video)

            # Sample interactions
            sampled_videos = random.sample(
                candidate_videos,
                min(num_interactions, len(candidate_videos))
            )

            for video in sampled_videos:
                # Determine interaction type based on user profile and video
                interaction = self._generate_single_interaction(user, video)
                interactions.append(interaction)
                self.event_count += 1

        logger.info(f"Generated {len(interactions)} interaction events")

        # Count event types
        event_types = {}
        for interaction in interactions:
            event_type = interaction['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

        logger.info("Event type distribution:")
        for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
            logger.info(f"  {event_type:15s}: {count:6d} ({count/len(interactions)*100:.1f}%)")

        return interactions

    def _generate_single_interaction(
        self,
        user: Dict,
        video: Dict
    ) -> Dict:
        """Generate a single user-video interaction."""

        video_duration = video['duration']
        user_avg_watch = user['avg_watch_time']
        user_skip_rate = user['skip_rate']
        user_interaction_rate = user['interaction_rate']

        # Determine if user skips
        if random.random() < user_skip_rate:
            # Skip: watch < 10% or < 3s
            watch_time = min(video_duration * 0.1, random.uniform(1, 3))
            return {
                'user_id': user['id'],
                'video_id': video['id'],
                'event_type': 'skip',
                'watch_time': watch_time,
                'video_duration': video_duration,
                'timestamp': (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat()
            }

        # Watch time (influenced by user avg and video quality)
        video_quality_factor = min(1.0, video['like_count'] / max(1, video['view_count']) / 0.15)
        base_watch_time = user_avg_watch * random.uniform(0.7, 1.3)
        quality_adjusted_watch_time = base_watch_time * (0.7 + 0.3 * video_quality_factor)
        watch_time = min(video_duration, quality_adjusted_watch_time)

        interaction = {
            'user_id': user['id'],
            'video_id': video['id'],
            'event_type': 'watch',
            'watch_time': watch_time,
            'video_duration': video_duration,
            'timestamp': (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat()
        }

        # Completion?
        if watch_time / video_duration >= 0.95:
            interaction['event_type'] = 'complete'

        # Engagement (like, comment, share)?
        if random.random() < user_interaction_rate:
            # Higher watch ratio = more likely to engage
            watch_ratio = watch_time / video_duration
            engagement_prob = user_interaction_rate * watch_ratio

            if random.random() < engagement_prob:
                engagement_type = random.choices(
                    ['like', 'comment', 'share'],
                    weights=[60, 30, 10]
                )[0]

                interaction['engaged'] = True
                interaction['engagement_type'] = engagement_type

        return interaction

    def save_to_files(
        self,
        users: List[Dict],
        videos: List[Dict],
        interactions: List[Dict],
        output_dir: str = "./sample_data"
    ):
        """
        Save generated data to JSON files.

        Args:
            users: List of users
            videos: List of videos
            interactions: List of interactions
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save users
        users_file = output_path / "users.json"
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        logger.info(f"Saved {len(users)} users to {users_file}")

        # Save videos
        videos_file = output_path / "videos.json"
        with open(videos_file, 'w') as f:
            json.dump(videos, f, indent=2)
        logger.info(f"Saved {len(videos)} videos to {videos_file}")

        # Save interactions
        interactions_file = output_path / "interactions.json"
        with open(interactions_file, 'w') as f:
            json.dump(interactions, f, indent=2)
        logger.info(f"Saved {len(interactions)} interactions to {interactions_file}")

        # Save summary
        summary = {
            'generated_at': datetime.now().isoformat(),
            'counts': {
                'users': len(users),
                'videos': len(videos),
                'interactions': len(interactions)
            },
            'statistics': {
                'avg_interactions_per_user': len(interactions) / len(users) if users else 0,
                'avg_interactions_per_video': len(interactions) / len(videos) if videos else 0
            }
        }

        summary_file = output_path / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved summary to {summary_file}")


def main():
    """Generate sample data for testing."""
    logger.info("="*70)
    logger.info("SAMPLE DATA GENERATOR")
    logger.info("="*70)

    generator = SampleDataGenerator(seed=42)

    # Generate data
    users = generator.generate_users(count=100)
    videos = generator.generate_videos(count=500)
    interactions = generator.generate_interactions(
        users=users,
        videos=videos,
        interactions_per_user=50
    )

    # Save to files
    generator.save_to_files(
        users=users,
        videos=videos,
        interactions=interactions,
        output_dir="./sample_data"
    )

    logger.info("\n" + "="*70)
    logger.info("GENERATION COMPLETE")
    logger.info("="*70)
    logger.info(f"Total users: {len(users)}")
    logger.info(f"Total videos: {len(videos)}")
    logger.info(f"Total interactions: {len(interactions)}")
    logger.info(f"\nData saved to: ./sample_data/")


if __name__ == "__main__":
    main()
