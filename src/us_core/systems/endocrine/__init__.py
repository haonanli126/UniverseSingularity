"""
Endocrine system: intrinsic motivation, emotion dynamics, reward integration.
"""

from .motivation import (
    IntrinsicMotivationConfig,
    IntrinsicMotivationSignal,
    compute_intrinsic_motivation,
)
from .reward import (
    RewardConfig,
    RewardComponents,
    combine_rewards,
    discount_return,
)
from .emotion import EmotionState, update_emotion, label_emotion

__all__ = [
    "IntrinsicMotivationConfig",
    "IntrinsicMotivationSignal",
    "compute_intrinsic_motivation",
    "RewardConfig",
    "RewardComponents",
    "combine_rewards",
    "discount_return",
    "EmotionState",
    "update_emotion",
    "label_emotion",
]
