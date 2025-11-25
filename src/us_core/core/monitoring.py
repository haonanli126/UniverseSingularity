from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Sequence


class PerformanceMetrics:
    """Lightweight metrics calculator over a digital embryo object.

    This is a simplified version of the blueprint's PerformanceMetrics, but
    keeps the same spirit and some metric names so we can later extend it.
    """

    # Learning related
    LEARNING_EFFICIENCY = "learning_efficiency"
    SAMPLE_EFFICIENCY = "sample_efficiency"

    # Decision related
    DECISION_ACCURACY = "decision_accuracy"

    # Consciousness related
    CONSCIOUSNESS_LEVEL = "consciousness_level"

    @classmethod
    def calculate_all_metrics(cls, embryo: Any) -> Dict[str, float]:
        """Calculate a small set of metrics from a given embryo-like object.

        The `embryo` is expected (duck-typed) to optionally expose:
        - learning_history: Iterable[float]
        - experience_usage: Iterable[float]
        - decision_accuracy: Iterable[float]
        - global_workspace: object with .last_winner.score in [0, 1]
        """
        metrics: Dict[str, float] = {}

        metrics[cls.LEARNING_EFFICIENCY] = cls._safe_mean(
            getattr(embryo, "learning_history", ()),
        )
        metrics[cls.SAMPLE_EFFICIENCY] = cls._safe_mean(
            getattr(embryo, "experience_usage", ()),
        )
        metrics[cls.DECISION_ACCURACY] = cls._safe_mean(
            getattr(embryo, "decision_accuracy", ()),
        )

        gw = getattr(embryo, "global_workspace", None)
        level = 0.0
        if gw is not None:
            last = getattr(gw, "last_winner", None)
            if last is not None:
                level = float(getattr(last, "score", 0.0))
        # clamp
        if level < 0.0:
            level = 0.0
        if level > 1.0:
            level = 1.0
        metrics[cls.CONSCIOUSNESS_LEVEL] = level

        return metrics

    # -------- helpers --------
    @staticmethod
    def _safe_mean(values: Iterable[float]) -> float:
        vals = [float(v) for v in values if not math.isnan(float(v))]
        if not vals:
            return 0.0
        return sum(vals) / len(vals)
