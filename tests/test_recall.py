from __future__ import annotations

"""
测试 events_to_dialogue 的行为：
- 能正确抽取 user / assistant 消息
- 能按顺序返回
- 能正确截断为最近 N 条
"""

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.recall import events_to_dialogue


def test_events_to_dialogue_basic_and_limit():
    e1 = EmbryoEvent(
        type=EventType.PERCEPTION,
        payload={"role": "user", "text": "hi"},
    )
    e2 = EmbryoEvent(
        type=EventType.SYSTEM,
        payload={"role": "assistant", "text": "hello"},
    )
    e3 = EmbryoEvent(
        type=EventType.SYSTEM,
        payload={"role": "assistant", "text": "extra"},
    )
    # 一个无效事件（没有 role/text）
    e4 = EmbryoEvent(type=EventType.SYSTEM, payload={"foo": "bar"})

    messages_all = events_to_dialogue([e1, e2, e3, e4], max_messages=None)
    assert len(messages_all) == 3
    assert messages_all[0]["role"] == "user"
    assert messages_all[0]["text"] == "hi"
    assert messages_all[1]["role"] == "assistant"
    assert messages_all[1]["text"] == "hello"
    assert messages_all[2]["text"] == "extra"

    messages_last_two = events_to_dialogue([e1, e2, e3, e4], max_messages=2)
    assert len(messages_last_two) == 2
    assert messages_last_two[0]["text"] == "hello"
    assert messages_last_two[1]["text"] == "extra"
