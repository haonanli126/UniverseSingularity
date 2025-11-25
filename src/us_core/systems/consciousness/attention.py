from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class AttentionSnapshot:
    """Single snapshot of attention allocation over named channels."""

    scores: Dict[str, float]


class AttentionFilter:
    """Filter out low-relevance candidates."""

    def __init__(self, min_relevance: float = 0.2) -> None:
        self.min_relevance = float(min_relevance)

    def filter(self, candidates: Dict[str, float]) -> Dict[str, float]:
        """Return only entries whose value >= min_relevance."""
        return {
            name: float(score)
            for name, score in candidates.items()
            if float(score) >= self.min_relevance
        }


class AttentionAllocator:
    """Normalize attention weights so they sum to 1.0."""

    def allocate(self, candidates: Dict[str, float]) -> Dict[str, float]:
        if not candidates:
            return {}

        values = {k: float(v) for k, v in candidates.items()}
        total = sum(values.values())
        if total <= 0.0:
            # fallback:均分
            n = len(values)
            return {k: 1.0 / n for k in values.keys()}

        return {k: v / total for k, v in values.items()}


class AttentionMonitor:
    """Keep a short history of attention allocations for introspection."""

    def __init__(self, max_history: int = 100) -> None:
        self.max_history = int(max_history)
        self._history: List[AttentionSnapshot] = []

    def record(self, scores: Dict[str, float]) -> None:
        snapshot = AttentionSnapshot(scores={k: float(v) for k, v in scores.items()})
        self._history.append(snapshot)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history :]

    @property
    def history(self) -> List[AttentionSnapshot]:
        # 返回拷贝，避免外部修改内部列表
        return list(self._history)
