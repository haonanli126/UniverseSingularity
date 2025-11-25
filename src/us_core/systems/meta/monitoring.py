# src/us_core/systems/meta/monitoring.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ThoughtStep:
    """单个思维步骤的记录，用于元认知监控。"""

    index: int
    description: str
    decision: str
    confidence: float
    outcome: Optional[bool] = None


class ThinkingMonitor:
    """记录思维步骤（决策链），方便事后复盘"""

    def __init__(self) -> None:
        self._steps: List[ThoughtStep] = []

    def log_step(self, description: str, decision: str, confidence: float) -> ThoughtStep:
        step = ThoughtStep(
            index=len(self._steps),
            description=description,
            decision=decision,
            confidence=confidence,
        )
        self._steps.append(step)
        return step

    def set_outcome(self, index: int, outcome: bool) -> None:
        if 0 <= index < len(self._steps):
            self._steps[index].outcome = outcome

    def all_steps(self) -> List[ThoughtStep]:
        return list(self._steps)


class ConfidenceCalibrator:
    """用 Brier score 粗略衡量信心校准程度"""

    def __init__(self) -> None:
        self._preds: List[float] = []
        self._outs: List[bool] = []

    def add_prediction(self, confidence: float, outcome: bool) -> None:
        self._preds.append(confidence)
        self._outs.append(outcome)

    def brier_score(self) -> float:
        if not self._preds:
            return 0.0
        errors = []
        for p, o in zip(self._preds, self._outs):
            y = 1.0 if o else 0.0
            errors.append((p - y) ** 2)
        return sum(errors) / len(errors)


class PerformanceTracker:
    """追踪每个 episode 的 reward，支持移动平均"""

    def __init__(self) -> None:
        self._rewards: List[float] = []

    def add_episode_reward(self, reward: float) -> None:
        self._rewards.append(float(reward))

    def moving_average(self, window: int = 10) -> List[float]:
        if window <= 1 or not self._rewards:
            return list(self._rewards)

        out: List[float] = []
        for i in range(len(self._rewards)):
            start = max(0, i - window + 1)
            segment = self._rewards[start : i + 1]
            out.append(sum(segment) / len(segment))
        return out
