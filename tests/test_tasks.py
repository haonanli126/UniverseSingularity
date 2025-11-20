from __future__ import annotations

"""
测试任务抽取与筛选逻辑（Task Board v0）
"""

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.tasks import (
    should_create_task,
    prepare_task_events,
    get_open_tasks,
    set_task_status,
)


def _user_event(text: str, label: str, confidence: float) -> EmbryoEvent:
    return EmbryoEvent(
        type=EventType.PERCEPTION,
        payload={
            "role": "user",
            "text": text,
            "intent": {
                "label": label,
                "confidence": confidence,
                "reason": "test",
            },
        },
    )


def test_should_create_task_rules():
    cmd_high = _user_event("帮我做一件事", "command", 0.9)
    cmd_low = _user_event("帮我做一件事", "command", 0.3)
    chat_ev = _user_event("随便聊聊", "chat", 0.9)

    assert should_create_task(cmd_high)
    assert not should_create_task(cmd_low)
    assert not should_create_task(chat_ev)


def test_prepare_task_events_and_dedup():
    e1 = _user_event("帮我写个脚本", "command", 0.9)
    e2 = _user_event("随便聊聊", "chat", 0.9)
    e3 = _user_event("帮我想一个任务清单", "command", 0.95)

    all_events = [e1, e2, e3]

    # 假设 e1 已经被记录为任务
    existing_task = EmbryoEvent(
        type=EventType.MEMORY,
        payload={
            "kind": "task",
            "status": "open",
            "text": "帮我写个脚本",
            "original_event_id": e1.id,
        },
    )

    new_tasks = prepare_task_events(all_events, [existing_task])

    # 只应该为 e3 生成新任务
    assert len(new_tasks) == 1
    t = new_tasks[0]
    assert t.payload["text"] == e3.payload["text"]
    assert t.payload["original_event_id"] == e3.id
    assert t.payload["kind"] == "task"
    assert t.payload["status"] == "open"


def test_get_open_tasks():
    open1 = EmbryoEvent(
        type=EventType.MEMORY,
        payload={"kind": "task", "status": "open", "text": "任务A"},
    )
    done = EmbryoEvent(
        type=EventType.MEMORY,
        payload={"kind": "task", "status": "done", "text": "任务B"},
    )
    open2 = EmbryoEvent(
        type=EventType.MEMORY,
        payload={"kind": "task", "text": "任务C"},
    )
    other = EmbryoEvent(
        type=EventType.MEMORY,
        payload={"kind": "note", "text": "not a task"},
    )

    open_tasks = get_open_tasks([open1, done, open2, other])
    texts = [t.payload["text"] for t in open_tasks]

    assert "任务A" in texts
    assert "任务C" in texts
    assert "任务B" not in texts
    assert "not a task" not in texts
    assert len(open_tasks) == 2

def test_set_task_status_update_by_id_and_original_event_id():
    # 用任务事件自身 id 更新
    t1 = EmbryoEvent(
        type=EventType.MEMORY,
        payload={"kind": "task", "status": "open", "text": "任务A"},
    )
    t2 = EmbryoEvent(
        type=EventType.MEMORY,
        payload={
            "kind": "task",
            "status": "open",
            "text": "任务B",
            "original_event_id": "orig-2",
        },
    )

    # 先用任务自身 id 把 t1 标记 done
    set_task_status([t1, t2], [t1.id], "done")
    assert t1.payload["status"] == "done"
    assert t2.payload["status"] == "open"

    # 再用 original_event_id 把 t2 标记 closed
    set_task_status([t1, t2], ["orig-2"], "closed")
    assert t2.payload["status"] == "closed"

