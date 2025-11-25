from __future__ import annotations

from dataclasses import dataclass


def _clamp01(value: float) -> float:
    """Clamp value into [0, 1]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass
class IntrinsicMotivationConfig:
    """Weights for different intrinsic drives.

    All inputs to `compute_intrinsic_motivation` are expected to be roughly in [0, 1],
    where higher = stronger signal.
    """

    curiosity_weight: float = 1.0
    mastery_weight: float = 1.0
    consistency_weight: float = 1.0


@dataclass
class IntrinsicMotivationSignal:
    """Decomposed intrinsic motivation signal."""
    curiosity: float
    mastery: float
    consistency: float

    @property
    def total(self) -> float:
        return self.curiosity + self.mastery + self.consistency


def compute_intrinsic_motivation(
    prediction_error: float,
    skill_progress: float,
    cognitive_dissonance: float,
    config: IntrinsicMotivationConfig | None = None,
) -> IntrinsicMotivationSignal:
    """Compute intrinsic motivation from three sources.

    Args:
        prediction_error: How surprising the world is (0-1). Higher -> more curiosity.
        skill_progress: How fast a skill is improving (0-1). Higher -> more mastery drive.
        cognitive_dissonance: Degree of internal conflict (0-1).
            Lower dissonance -> higher consistency reward.
        config: Optional weighting configuration.

    Returns:
        IntrinsicMotivationSignal with each component clamped to [0, 1].
    """
    if config is None:
        config = IntrinsicMotivationConfig()

    curiosity = _clamp01(prediction_error * config.curiosity_weight)
    mastery = _clamp01(skill_progress * config.mastery_weight)

    # We want low dissonance to be rewarding, so invert it.
    consistency_raw = (1.0 - _clamp01(cognitive_dissonance)) * config.consistency_weight
    consistency = _clamp01(consistency_raw)

    return IntrinsicMotivationSignal(
        curiosity=curiosity,
        mastery=mastery,
        consistency=consistency,
    )
