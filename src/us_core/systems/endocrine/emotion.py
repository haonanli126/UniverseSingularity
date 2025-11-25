from __future__ import annotations

from dataclasses import dataclass
import math

from .reward import RewardComponents


def _clamp_neg1_1(value: float) -> float:
    if value < -1.0:
        return -1.0
    if value > 1.0:
        return 1.0
    return value


def _clamp01_like_decay(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass
class EmotionState:
    """Simple PAD-like emotion representation.

    valence: pleasantness (-1..1)
    arousal: activation (-1..1, usually 0..1 in practice)
    dominance: sense of control (-1..1)
    """

    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0


def update_emotion(
    state: EmotionState,
    reward: RewardComponents,
    decay: float = 0.9,
) -> EmotionState:
    """Update emotion state based on recent reward.

    The larger and more positive the total reward, the more positive valence and
    higher arousal become. Negative rewards lower valence and can still raise
    arousal (stress).
    """
    decay = _clamp01_like_decay(decay)

    total_reward = reward.total

    # Target valence: squashed into [-1, 1]
    target_valence = math.tanh(total_reward)
    new_valence = _clamp_neg1_1(
        state.valence * decay + target_valence * (1.0 - decay)
    )

    # Arousal depends on magnitude of change, not just sign.
    target_arousal = min(1.0, abs(total_reward))
    new_arousal = _clamp_neg1_1(
        state.arousal * decay + target_arousal * (1.0 - decay)
    )

    # Dominance: positive rewards increase sense of control, negative decrease.
    target_dom = math.tanh(total_reward * 0.5)
    new_dom = _clamp_neg1_1(
        state.dominance * decay + target_dom * (1.0 - decay)
    )

    return EmotionState(valence=new_valence, arousal=new_arousal, dominance=new_dom)


def label_emotion(state: EmotionState) -> str:
    """Map continuous state to a coarse emotion label."""
    v = state.valence
    a = state.arousal

    if abs(v) < 0.15 and a < 0.2:
        return "neutral"

    if v >= 0.2 and a >= 0.4:
        return "excited"

    if v >= 0.2 and a < 0.4:
        return "calm"

    if v <= -0.2 and a >= 0.4:
        return "angry"

    if v <= -0.2 and a < 0.4:
        return "sad"

    return "mixed"
