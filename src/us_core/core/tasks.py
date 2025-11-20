from __future__ import annotations

"""
任务抽取与查看（Task Board 核心逻辑 v0）

- 从会话事件中挑出「值得作为任务记录」的用户发言
- 规则：
  - 只考虑 type == PERCEPTION 且 payload.role == "user"
  - intent.label == "command"
  - intent.confidence >= 0.7
- 生成新的 EmbryoEvent（type=MEMORY，payload.kind="task"）
- 支持基于 original_event_id 去重
"""

from typing import Iterable, List, Optional, Set

from .events import EmbryoEvent, EventType


def _get_intent(payload: dict) -> tuple[Optional[str], float]:
    intent = payload.get("intent") or {}
    label = intent.get("label")
    conf = intent.get("confidence")

    label_str = label if isinstance(label, str) else None
    try:
        conf_val = float(conf)
    except (TypeError, ValueError):
        conf_val = 0.0

    return label_str, conf_val


def should_create_task(event: EmbryoEvent) -> bool:
    """
    判断一条事件是否应该被抽取成任务。
    """
    if event.type is not EventType.PERCEPTION:
        return False

    payload = event.payload or {}
    if payload.get("role") != "user":
        return False

    label, conf = _get_intent(payload)
    if label != "command":
        return False
    if conf < 0.7:
        return False

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return False

    return True


def prepare_task_events(
    all_events: Iterable[EmbryoEvent],
    existing_task_events: Iterable[EmbryoEvent],
) -> List[EmbryoEvent]:
    """
    基于所有会话事件 + 已有任务事件，生成本轮需要新增的任务事件列表。

    - 使用 payload.original_event_id 做去重
    - 新任务事件使用：
      type = MEMORY
      payload = {
        kind: "task",
        status: "open",
        text: 原始用户文本,
        intent: 原始 intent,
        original_event_id: 原事件 id,
        source: "task_collector",
      }
    """
    existing_ids: Set[str] = set()
    for e in existing_task_events:
        payload = e.payload or {}
        origin_id = payload.get("original_event_id")
        if isinstance(origin_id, str):
            existing_ids.add(origin_id)

    new_tasks: List[EmbryoEvent] = []

    for e in all_events:
        if not should_create_task(e):
            continue

        if e.id in existing_ids:
            # 已经作为任务记录过
            continue

        payload = e.payload or {}
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            continue

        task_event = EmbryoEvent(
            type=EventType.MEMORY,
            payload={
                "kind": "task",
                "status": "open",
                "text": text,
                "intent": payload.get("intent"),
                "original_event_id": e.id,
                "source": "task_collector",
            },
        )
        new_tasks.append(task_event)

    return new_tasks


def get_open_tasks(task_events: Iterable[EmbryoEvent]) -> List[EmbryoEvent]:
    """
    从任务事件中筛出「未完成任务」。

    约定：
    - payload.kind == "task"
    - payload.status 缺失或非 done/closed/cancelled/canceled → 视为 open
    """
    open_tasks: List[EmbryoEvent] = []

    for e in task_events:
        if e.type is not EventType.MEMORY:
            continue

        payload = e.payload or {}
        if payload.get("kind") != "task":
            continue

        status = str(payload.get("status") or "open").lower()
        if status in {"done", "closed", "cancelled", "canceled"}:
            continue

        open_tasks.append(e)

    return open_tasks

def set_task_status(
    all_events: Iterable[EmbryoEvent],
    target_ids: List[str],
    new_status: str,
) -> None:
    """
    在内存中更新任务事件的 status 字段（原地修改，不负责写回文件）。

    - all_events: 从 tasks.jsonl 读出的全部事件列表
    - target_ids: 希望更新的任务事件 id 列表（task 事件本身的 id，
                  或者 original_event_id，对应最初的用户事件 id）
    - new_status: 例如 "done" / "closed" / "cancelled"
    """
    id_set = set(target_ids)
    status_value = str(new_status).lower()

    for e in all_events:
        if e.type is not EventType.MEMORY:
            continue

        payload = e.payload or {}
        if payload.get("kind") != "task":
            continue

        # 支持用任务事件自身 id 或 original_event_id 匹配
        if e.id in id_set or payload.get("original_event_id") in id_set:
            payload["status"] = status_value
            e.payload = payload
