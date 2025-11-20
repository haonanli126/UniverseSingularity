from __future__ import annotations

"""
测试规划事件管理（Plans v0）
"""

from datetime import datetime, timedelta, timezone

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.plans import create_plan_event, get_recent_plans


def test_create_plan_event_basic():
    event = create_plan_event(
        summary="简单规划",
        full_text="这是一次测试规划内容。",
        related_task_ids=["id1", "id2"],
    )

    assert event.type == EventType.MEMORY
    payload = event.payload or {}
    assert payload["kind"] == "plan"
    assert payload["summary"] == "简单规划"
    assert payload["text"] == "这是一次测试规划内容。"
    assert payload["related_task_ids"] == ["id1", "id2"]
    assert payload["source"] == "planning_session"


def test_get_recent_plans_order_and_limit():
    now = datetime.now(timezone.utc)

    older = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=10),
        payload={
            "kind": "plan",
            "summary": "旧规划",
            "text": "old",
            "related_task_ids": [],
        },
    )
    newer = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={
            "kind": "plan",
            "summary": "新规划",
            "text": "new",
            "related_task_ids": [],
        },
    )
    other = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={
            "kind": "note",
            "summary": "不是规划",
        },
    )

    plans = get_recent_plans([older, newer, other], limit=1)
    assert len(plans) == 1
    assert plans[0].summary == "新规划"
    assert plans[0].text == "new"
