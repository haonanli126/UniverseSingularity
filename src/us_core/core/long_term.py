from __future__ import annotations

"""
长期记忆筛选器 v0：

- 从会话事件中挑选「值得长期记住」的用户发言
- 规则基于 intent：
  - PROJECT / META: 一律进入长期记忆
  - EMOTION 且可信度较高：进入长期记忆
  - COMMAND 且可信度较高：可选进入（这里先视为重要）
  - CHAT / UNKNOWN: 不进入长期记忆

- 输出为新的 EmbryoEvent：
  type = MEMORY
  payload:
    - role: "user"
    - text: 原始文本
    - intent: 原始 intent
    - original_event_id: 原事件 ID（用于去重）
"""

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from .events import EmbryoEvent, EventType


def _extract_intent_label(payload: dict) -> Optional[str]:
    intent = payload.get("intent") or {}
    label = intent.get("label")
    if not isinstance(label, str):
        return None
    return label


def _extract_intent_confidence(payload: dict) -> float:
    intent = payload.get("intent") or {}
    conf = intent.get("confidence")
    try:
        return float(conf)
    except (TypeError, ValueError):
        return 0.0


def should_archive_event(event: EmbryoEvent) -> bool:
    """
    判断一条事件是否应当进入长期记忆。
    只考虑：
    - type == PERCEPTION
    - payload.role == "user"
    再结合 intent 规则。
    """
    if event.type is not EventType.PERCEPTION:
        return False

    payload = event.payload or {}
    if payload.get("role") != "user":
        return False

    label = _extract_intent_label(payload)
    conf = _extract_intent_confidence(payload)

    if label is None:
        return False

    # PROJECT / META：一律视为重要
    if label in {"project", "meta"}:
        return True

    # EMOTION：情绪强烈时保留
    if label == "emotion" and conf >= 0.6:
        return True

    # COMMAND：高置信度时保留（重要任务请求）
    if label == "command" and conf >= 0.8:
        return True

    # CHAT / UNKNOWN：暂不进入长期记忆
    return False


def prepare_long_term_events(
    all_events: Iterable[EmbryoEvent],
    existing_archive_events: Iterable[EmbryoEvent],
) -> List[EmbryoEvent]:
    """
    基于现有会话事件 + 已有长期记忆事件，构造本轮需要追加的长期记忆事件列表。

    去重策略：
    - existing_archive_events 中若已有 payload.original_event_id，则跳过对应原始事件
    """
    existing_ids: Set[str] = set()
    for e in existing_archive_events:
        payload = e.payload or {}
        origin_id = payload.get("original_event_id")
        if isinstance(origin_id, str):
            existing_ids.add(origin_id)

    new_archive_events: List[EmbryoEvent] = []

    for e in all_events:
        if not should_archive_event(e):
            continue

        if e.id in existing_ids:
            # 已经归档过
            continue

        payload = e.payload or {}
        text = payload.get("text")
        if not text:
            continue

        archive_event = EmbryoEvent(
            type=EventType.MEMORY,
            payload={
                "role": "user",
                "text": text,
                "intent": payload.get("intent"),
                "original_event_id": e.id,
                "source": "long_term_selector",
            },
        )
        new_archive_events.append(archive_event)

    return new_archive_events
def get_recent_archive_events(
    archive_events: Iterable[EmbryoEvent],
    limit: int = 10,
) -> List[EmbryoEvent]:
    """
    从已有的长期记忆事件中，按时间倒序取最近 N 条。
    """
    sorted_events = sorted(
        archive_events,
        key=lambda e: e.timestamp,
        reverse=True,
    )
    return sorted_events[:limit]
