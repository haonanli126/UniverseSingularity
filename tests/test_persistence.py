from __future__ import annotations

"""
测试事件持久化的基本行为：

- 写入多条事件
- 按顺序读回
"""

from pathlib import Path

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.persistence import (
    append_event_to_jsonl,
    load_events_from_jsonl,
)


def test_append_and_load_events(tmp_path: Path):
    log_path = tmp_path / "events.jsonl"

    e1 = EmbryoEvent(type=EventType.PERCEPTION, payload={"text": "hello"})
    e2 = EmbryoEvent(type=EventType.SYSTEM, payload={"text": "world"})

    append_event_to_jsonl(log_path, e1)
    append_event_to_jsonl(log_path, e2)

    loaded = load_events_from_jsonl(log_path)

    assert len(loaded) == 2
    assert loaded[0].payload["text"] == "hello"
    assert loaded[1].payload["text"] == "world"
    assert loaded[0].type == EventType.PERCEPTION
    assert loaded[1].type == EventType.SYSTEM
