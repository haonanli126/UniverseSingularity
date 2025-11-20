from __future__ import annotations

"""
规划事件管理（Plans v0）

- create_plan_event: 把一次规划内容封装为 EmbryoEvent
- get_recent_plans: 从规划事件中提取最近 N 条，便于展示
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from .events import EmbryoEvent, EventType


@dataclass
class PlanItem:
    summary: str
    text: str
    related_task_ids: List[str]
    timestamp: datetime


def create_plan_event(
    summary: str,
    full_text: str,
    related_task_ids: Optional[List[str]] = None,
) -> EmbryoEvent:
    """
    构造一条规划事件，约定：
    - type = MEMORY
    - payload.kind = "plan"
    """
    return EmbryoEvent(
        type=EventType.MEMORY,
        payload={
            "kind": "plan",
            "summary": summary,
            "text": full_text,
            "related_task_ids": list(related_task_ids or []),
            "source": "planning_session",
        },
    )


def _iter_plan_items(events: Iterable[EmbryoEvent]) -> List[PlanItem]:
    items: List[PlanItem] = []
    for e in events:
        if e.type is not EventType.MEMORY:
            continue
        payload = e.payload or {}
        if payload.get("kind") != "plan":
            continue

        summary = str(payload.get("summary") or "")
        text = str(payload.get("text") or "")
        raw_ids = payload.get("related_task_ids") or []
        if not isinstance(raw_ids, list):
            raw_ids = []
        ids = [str(x) for x in raw_ids]

        items.append(
            PlanItem(
                summary=summary,
                text=text,
                related_task_ids=ids,
                timestamp=e.timestamp,
            )
        )
    return items


def get_recent_plans(
    events: Iterable[EmbryoEvent],
    limit: int = 5,
) -> List[PlanItem]:
    """
    从一批事件中筛出规划事件，按时间倒序取最近 N 条。
    """
    items = _iter_plan_items(events)
    items_sorted = sorted(items, key=lambda it: it.timestamp, reverse=True)
    return items_sorted[:limit]
