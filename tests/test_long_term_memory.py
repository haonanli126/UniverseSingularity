from __future__ import annotations

"""
测试长期记忆筛选器：

- 只选出满足规则的用户 PERCEPTION 事件
- 会生成 MEMORY 类型的新事件
- 支持基于 original_event_id 的去重
"""

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.long_term import (
    prepare_long_term_events,
    should_archive_event,
    get_recent_archive_events,
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


def test_should_archive_event_rules():
    e_chat = _user_event("随便聊聊", "chat", 0.6)
    e_project = _user_event("我们下一步的 Phase 1 做什么？", "project", 0.5)
    e_meta = _user_event("你还记得我们第一次聊的吗？", "meta", 0.5)
    e_emotion_low = _user_event("有点心情不好", "emotion", 0.4)
    e_emotion_high = _user_event("最近很难过", "emotion", 0.9)
    e_command_low = _user_event("帮我想想行不行？", "command", 0.5)
    e_command_high = _user_event("帮我列一个详细的任务清单", "command", 0.9)

    assert not should_archive_event(e_chat)
    assert should_archive_event(e_project)
    assert should_archive_event(e_meta)
    assert not should_archive_event(e_emotion_low)
    assert should_archive_event(e_emotion_high)
    assert not should_archive_event(e_command_low)
    assert should_archive_event(e_command_high)


def test_prepare_long_term_events_and_dedup():
    e_project = _user_event("项目相关", "project", 0.9)
    e_emotion = _user_event("真的有点累", "emotion", 0.9)
    e_chat = _user_event("哈哈，随便聊聊", "chat", 0.6)

    all_events = [e_project, e_emotion, e_chat]

    # 假设 e_project 已经被归档过
    existing_archive = [
        EmbryoEvent(
            type=EventType.MEMORY,
            payload={
                "original_event_id": e_project.id,
                "text": e_project.payload["text"],
            },
        )
    ]

    new_archive_events = prepare_long_term_events(all_events, existing_archive)

    # 只应该归档 e_emotion（project 已存在，chat 不需要）
    assert len(new_archive_events) == 1
    archived = new_archive_events[0]

    assert archived.type == EventType.MEMORY
    assert archived.payload["text"] == e_emotion.payload["text"]
    assert archived.payload["original_event_id"] == e_emotion.id
    assert archived.payload.get("intent") is not None


from datetime import datetime, timedelta, timezone


def test_get_recent_archive_events_order():
    now = datetime.now(timezone.utc)

    old = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=10),
        payload={"text": "old"},
    )
    middle = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=5),
        payload={"text": "middle"},
    )
    latest = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={"text": "latest"},
    )

    events = [old, middle, latest]

    recent = get_recent_archive_events(events, limit=2)
    assert len(recent) == 2
    # 应该按时间倒序：latest 在前，middle 在后
    assert recent[0].payload["text"] == "latest"
    assert recent[1].payload["text"] == "middle"
