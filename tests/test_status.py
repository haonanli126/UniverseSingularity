from __future__ import annotations

"""
测试状态统计模块：

- 对话日志统计
- 自省日志统计
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.persistence import append_event_to_jsonl
from src.us_core.core.status import (
    ConversationStats,
    ReflectionStats,
    get_conversation_stats,
    get_reflection_stats,
)


def _make_ts(offset_seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)


def test_get_conversation_stats(tmp_path: Path):
    log_path = tmp_path / "session_log.jsonl"

    # 写三条事件，其中两条带 role/text
    e1 = EmbryoEvent(
        type=EventType.PERCEPTION,
        timestamp=_make_ts(-10),
        payload={"role": "user", "text": "hello"},
    )
    e2 = EmbryoEvent(
        type=EventType.SYSTEM,
        timestamp=_make_ts(-5),
        payload={"role": "assistant", "text": "hi"},
    )
    e3 = EmbryoEvent(
        type=EventType.SYSTEM,
        timestamp=_make_ts(0),
        payload={"foo": "bar"},
    )

    append_event_to_jsonl(log_path, e1)
    append_event_to_jsonl(log_path, e2)
    append_event_to_jsonl(log_path, e3)

    stats: ConversationStats = get_conversation_stats(log_path)

    assert stats.total_events == 3
    assert stats.total_messages == 2
    assert stats.last_timestamp is not None
    # last_timestamp 应该是 e3 的时间（最大）
    assert abs(stats.last_timestamp.timestamp() - e3.timestamp.timestamp()) < 1.0


def test_get_reflection_stats(tmp_path: Path):
    log_path = tmp_path / "reflections.jsonl"

    e1 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=_make_ts(-20),
        payload={"kind": "reflection", "text": "old"},
    )
    e2 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=_make_ts(-5),
        payload={"kind": "reflection", "text": "new"},
    )

    append_event_to_jsonl(log_path, e1)
    append_event_to_jsonl(log_path, e2)

    stats: ReflectionStats = get_reflection_stats(log_path)

    assert stats.total_events == 2
    assert stats.last_timestamp is not None
    assert abs(stats.last_timestamp.timestamp() - e2.timestamp.timestamp()) < 1.0
