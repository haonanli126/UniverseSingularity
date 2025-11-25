from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .broadcast import BroadcastSystem


def _clamp01(value: float) -> float:
    """Clamp a float into [0, 1]."""
    v = float(value)
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


@dataclass
class WorkspaceItem:
    """A single candidate piece of content competing for consciousness."""

    source: str
    content: str
    newness: float
    relevance: float
    affect: float
    goal_alignment: float

    @property
    def score(self) -> float:
        """Weighted score, following blueprint weights.

        newness 0.3, relevance 0.3, affect (valence) 0.2, goal alignment 0.2
        """
        return (
            0.3 * self.newness
            + 0.3 * self.relevance
            + 0.2 * self.affect
            + 0.2 * self.goal_alignment
        )


class GlobalWorkspaceSystem:
    """Implements the global workspace competition & broadcasting.

    Usage:
        gw = GlobalWorkspaceSystem(min_score=0.3)
        result = gw.compete_and_broadcast(inputs)

    Where `inputs` is a dict like:
        {
            "sensory": {
                "content": "看到红色物体",
                "newness": 0.8,
                "relevance": 0.7,
                "affect": 0.5,
                "goal_alignment": 0.6,
            },
            "memory": {...},
        }
    """

    def __init__(
        self,
        min_score: float = 0.0,
        broadcaster: Optional[BroadcastSystem] = None,
    ) -> None:
        self.min_score = min_score
        self.broadcaster = broadcaster
        self.last_winner: Optional[WorkspaceItem] = None

    # -------- internal helpers --------
    def _coerce_item(self, source: str, payload: Dict[str, Any]) -> WorkspaceItem:
        content = str(payload.get("content", ""))

        newness = _clamp01(payload.get("newness", payload.get("novelty", 0.5)))
        relevance = _clamp01(payload.get("relevance", 0.5))
        affect = _clamp01(payload.get("affect", payload.get("emotion", 0.5)))
        goal_alignment = _clamp01(payload.get("goal_alignment", payload.get("goal_score", 0.5)))

        return WorkspaceItem(
            source=source,
            content=content,
            newness=newness,
            relevance=relevance,
            affect=affect,
            goal_alignment=goal_alignment,
        )

    # -------- public API --------
    def compete(self, inputs: Dict[str, Dict[str, Any]]) -> List[WorkspaceItem]:
        """Convert raw inputs into WorkspaceItems and rank them."""
        items = [self._coerce_item(source, payload) for source, payload in inputs.items()]
        items.sort(key=lambda it: it.score, reverse=True)
        return items

    def compete_and_broadcast(
        self, inputs: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Run competition and optionally broadcast the winning content.

        Returns a lightweight dict describing the result, or None if
        no candidate passes the min_score threshold.
        """
        ranked = self.compete(inputs)
        if not ranked:
            self.last_winner = None
            return None

        winner = ranked[0]
        if winner.score < self.min_score:
            self.last_winner = None
            return None

        self.last_winner = winner

        result = {
            "content": winner.content,
            "source": winner.source,
            "score": winner.score,
            "candidates": [
                {"source": it.source, "content": it.content, "score": it.score}
                for it in ranked
            ],
        }

        if self.broadcaster is not None:
            # 这里不关心订阅者内部逻辑，只负责把结果扔出去
            self.broadcaster.broadcast(result)

        return result
