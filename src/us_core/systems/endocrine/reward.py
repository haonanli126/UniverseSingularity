from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class RewardConfig:
    """Configuration for combining intrinsic and extrinsic reward."""
    gamma: float = 0.99
    intrinsic_weight: float = 0.1


@dataclass
class RewardComponents:
    """Decomposed reward used by the endocrine system."""
    extrinsic: float
    intrinsic: float

    @property
    def total(self) -> float:
        return self.extrinsic + self.intrinsic


def combine_rewards(
    extrinsic: float,
    intrinsic_total: float,
    config: RewardConfig | None = None,
) -> RewardComponents:
    """Combine raw extrinsic reward and intrinsic motivation into a usable signal.

    Args:
        extrinsic: Reward directly from the environment.
        intrinsic_total: Scalar intrinsic reward (e.g. from IntrinsicMotivationSignal.total).
        config: Optional weighting configuration.

    Returns:
        RewardComponents with separate and total views.
    """
    if config is None:
        config = RewardConfig()

    intrinsic_scaled = intrinsic_total * config.intrinsic_weight
    return RewardComponents(extrinsic=extrinsic, intrinsic=intrinsic_scaled)


def discount_return(rewards: Sequence[float], gamma: float = 0.99) -> float:
    """Compute discounted return for a sequence of rewards."""
    total = 0.0
    discount = 1.0
    for r in rewards:
        total += discount * r
        discount *= gamma
    return total
