"""
Training Script for Video Scoring Model

This script trains the AI-based video scoring model with configurable weights
for different objectives (engagement, retention, discovery, monetization).

Training data comes from user interaction events stored in SurrealDB.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
import os
from datetime import datetime, timedelta
import logging

from ..models.video_scorer import VideoScoringModel, MultiObjectiveVideoScorer
from ..features.feature_engineering import VideoFeatureExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoInteractionDataset(Dataset):
    """
    Dataset for training video scoring model from user interaction events.

    Each sample represents a user-video interaction with:
    - Video features (CLIP embeddings, metadata)
    - User features (preferences, history)
    - Interaction features (views, likes, etc.)
    - Label: Engagement score (watch_time_ratio, interaction_type, etc.)
    """

    def __init__(
        self,
        interactions: List[Dict],
        feature_extractor: VideoFeatureExtractor,
        label_type: str = 'watch_time'
    ):
        """
        Initialize dataset from interaction events.

        Args:
            interactions: List of interaction dicts with video, user, and event data
            feature_extractor: Feature extraction instance
            label_type: Type of label to predict ('watch_time', 'engagement', 'retention')
        """
        self.interactions = interactions
        self.feature_extractor = feature_extractor
        self.label_type = label_type

    def __len__(self) -> int:
        return len(self.interactions)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get a single training sample.

        Returns:
            clip_embeddings: (512,) tensor
            interaction_features: (8,) tensor
            user_features: (6,) tensor
            label: (1,) tensor
        """
        interaction = self.interactions[idx]

        # Extract features
        clip_emb, inter_feat, user_feat = self.feature_extractor.extract_all_features(
            video_data=interaction['video'],
            user_data=interaction['user'],
            user_history=interaction.get('user_history', [])
        )

        # Extract label based on label_type
        if self.label_type == 'watch_time':
            # Watch time ratio as label [0, 1]
            duration = interaction['video'].get('duration', 1)
            watch_time = interaction.get('watch_time', 0)
            label = min(1.0, watch_time / duration)

        elif self.label_type == 'engagement':
            # Engagement score: weighted combination of interactions
            liked = 1.0 if interaction.get('liked') else 0.0
            commented = 1.0 if interaction.get('commented') else 0.0
            shared = 1.0 if interaction.get('shared') else 0.0
            watch_ratio = min(1.0, interaction.get('watch_time', 0) / interaction['video'].get('duration', 1))

            # Weighted engagement score
            label = (
                watch_ratio * 0.3 +
                liked * 0.3 +
                commented * 0.2 +
                shared * 0.2
            )

        elif self.label_type == 'retention':
            # Binary retention: did user watch >= 50% of video
            duration = interaction['video'].get('duration', 1)
            watch_time = interaction.get('watch_time', 0)
            label = 1.0 if (watch_time / duration) >= 0.5 else 0.0

        else:
            label = 0.0

        return (
            torch.from_numpy(clip_emb),
            torch.from_numpy(inter_feat),
            torch.from_numpy(user_feat),
            torch.tensor([label], dtype=torch.float32)
        )


class VideoScorerTrainer:
    """Trainer for video scoring models with configurable weights."""

    def __init__(
        self,
        model_type: str = 'single',  # 'single' or 'multi_objective'
        weight_config: Optional[Dict[str, float]] = None,
        learning_rate: float = 0.001,
        device: str = 'cpu'
    ):
        """
        Initialize trainer.

        Args:
            model_type: 'single' for VideoScoringModel or 'multi_objective' for MultiObjectiveVideoScorer
            weight_config: Configuration for feature weights
            learning_rate: Learning rate for optimizer
            device: 'cpu' or 'cuda'
        """
        self.model_type = model_type
        self.weight_config = weight_config
        self.learning_rate = learning_rate
        self.device = torch.device(device)

        # Initialize model
        if model_type == 'single':
            self.model = VideoScoringModel(
                weight_config=weight_config
            ).to(self.device)
        else:
            self.model = MultiObjectiveVideoScorer().to(self.device)

        # Initialize optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=1e-5
        )

        # Loss function (MSE for regression, BCE for binary classification)
        self.criterion = nn.MSELoss()

        # Feature extractor
        self.feature_extractor = VideoFeatureExtractor(weight_config)

        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'tower_weights': []
        }

    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> float:
        """
        Train for one epoch.

        Args:
            train_loader: DataLoader for training data
            epoch: Current epoch number

        Returns:
            avg_loss: Average training loss for the epoch
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, (clip_emb, inter_feat, user_feat, labels) in enumerate(train_loader):
            # Move to device
            clip_emb = clip_emb.to(self.device)
            inter_feat = inter_feat.to(self.device)
            user_feat = user_feat.to(self.device)
            labels = labels.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            predictions = self.model(clip_emb, inter_feat, user_feat)

            # Compute loss
            loss = self.criterion(predictions, labels)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

            if batch_idx % 100 == 0:
                logger.info(f"Epoch {epoch}, Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / num_batches
        return avg_loss

    def validate(
        self,
        val_loader: DataLoader
    ) -> float:
        """
        Validate the model.

        Args:
            val_loader: DataLoader for validation data

        Returns:
            avg_loss: Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for clip_emb, inter_feat, user_feat, labels in val_loader:
                # Move to device
                clip_emb = clip_emb.to(self.device)
                inter_feat = inter_feat.to(self.device)
                user_feat = user_feat.to(self.device)
                labels = labels.to(self.device)

                # Forward pass
                predictions = self.model(clip_emb, inter_feat, user_feat)

                # Compute loss
                loss = self.criterion(predictions, labels)
                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches
        return avg_loss

    def train(
        self,
        train_dataset: VideoInteractionDataset,
        val_dataset: Optional[VideoInteractionDataset] = None,
        epochs: int = 10,
        batch_size: int = 32,
        save_dir: str = './models/checkpoints'
    ):
        """
        Train the model for multiple epochs.

        Args:
            train_dataset: Training dataset
            val_dataset: Optional validation dataset
            epochs: Number of training epochs
            batch_size: Batch size for training
            save_dir: Directory to save model checkpoints
        """
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4
        )

        val_loader = None
        if val_dataset:
            val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=4
            )

        # Create save directory
        os.makedirs(save_dir, exist_ok=True)

        best_val_loss = float('inf')

        logger.info(f"Starting training for {epochs} epochs...")
        logger.info(f"Training samples: {len(train_dataset)}")
        if val_dataset:
            logger.info(f"Validation samples: {len(val_dataset)}")

        for epoch in range(1, epochs + 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"Epoch {epoch}/{epochs}")
            logger.info(f"{'='*50}")

            # Train
            train_loss = self.train_epoch(train_loader, epoch)
            self.history['train_loss'].append(train_loss)

            logger.info(f"Train Loss: {train_loss:.4f}")

            # Validate
            if val_loader:
                val_loss = self.validate(val_loader)
                self.history['val_loss'].append(val_loss)
                logger.info(f"Val Loss: {val_loss:.4f}")

                # Save best model
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    self.save_model(os.path.join(save_dir, 'best_model.pt'))
                    logger.info("Saved best model!")

            # Log tower weights for single objective model
            if self.model_type == 'single':
                weights = self.model.get_tower_weights()
                self.history['tower_weights'].append(weights)
                logger.info(f"Tower weights: {weights}")

            # Save checkpoint
            if epoch % 5 == 0:
                self.save_model(os.path.join(save_dir, f'model_epoch_{epoch}.pt'))

        # Save final model
        self.save_model(os.path.join(save_dir, 'final_model.pt'))
        logger.info("Training complete!")

    def save_model(self, path: str):
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'weight_config': self.weight_config,
            'model_type': self.model_type,
            'history': self.history
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.weight_config = checkpoint.get('weight_config')
        self.history = checkpoint.get('history', self.history)
        logger.info(f"Model loaded from {path}")


def create_training_config(objective: str = 'engagement') -> Dict[str, float]:
    """
    Create weight configuration for different training objectives.

    Args:
        objective: 'engagement', 'retention', 'discovery', or 'monetization'

    Returns:
        weight_config: Dictionary of feature weights
    """
    configs = {
        'engagement': {
            'content_weight': 0.25,
            'interaction_weight': 0.50,
            'user_weight': 0.25,
            'view_weight': 1.0,
            'like_weight': 8.0,
            'comment_weight': 10.0,
            'share_weight': 12.0,
            'freshness_decay': 24.0,
            'watch_time_multiplier': 1.5
        },
        'retention': {
            'content_weight': 0.35,
            'interaction_weight': 0.30,
            'user_weight': 0.35,
            'view_weight': 1.0,
            'like_weight': 5.0,
            'comment_weight': 6.0,
            'share_weight': 7.0,
            'freshness_decay': 48.0,
            'watch_time_multiplier': 3.0
        },
        'discovery': {
            'content_weight': 0.40,
            'interaction_weight': 0.30,
            'user_weight': 0.30,
            'view_weight': 1.0,
            'like_weight': 4.0,
            'comment_weight': 5.0,
            'share_weight': 6.0,
            'freshness_decay': 12.0,
            'watch_time_multiplier': 1.0
        },
        'monetization': {
            'content_weight': 0.30,
            'interaction_weight': 0.35,
            'user_weight': 0.35,
            'view_weight': 1.0,
            'like_weight': 6.0,
            'comment_weight': 8.0,
            'share_weight': 10.0,
            'freshness_decay': 36.0,
            'watch_time_multiplier': 2.0
        }
    }

    return configs.get(objective, configs['engagement'])


if __name__ == '__main__':
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Train video scoring model')
    parser.add_argument('--objective', type=str, default='engagement',
                        choices=['engagement', 'retention', 'discovery', 'monetization'],
                        help='Training objective')
    parser.add_argument('--model_type', type=str, default='single',
                        choices=['single', 'multi_objective'],
                        help='Model type')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001,
                        help='Learning rate')
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help='Device to train on')
    parser.add_argument('--save_dir', type=str, default='./models/checkpoints',
                        help='Directory to save checkpoints')

    args = parser.parse_args()

    # Create weight configuration
    weight_config = create_training_config(args.objective)

    logger.info(f"Training with {args.objective} objective")
    logger.info(f"Weight configuration: {json.dumps(weight_config, indent=2)}")

    # Initialize trainer
    trainer = VideoScorerTrainer(
        model_type=args.model_type,
        weight_config=weight_config,
        learning_rate=args.lr,
        device=args.device
    )

    # TODO: Load actual training data from SurrealDB
    # This would require implementing data collection from user interaction events
    logger.warning("Training data loading not implemented - need to collect interaction events from SurrealDB")
