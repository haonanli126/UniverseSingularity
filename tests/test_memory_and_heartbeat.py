from __future__ import annotations

"""
测试 MemoryBuffer 的基础行为：
- 容量限制
- 先进先出
"""

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.memory import MemoryBuffer


def test_memory_buffer_fifo_and_limit():
    buffer = MemoryBuffer(max_events=2)

    e1 = EmbryoEvent(type=EventType.SYSTEM, payload={"n": 1})
    e2 = EmbryoEvent(type=EventType.SYSTEM, payload={"n": 2})
    e3 = EmbryoEvent(type=EventType.SYSTEM, payload={"n": 3})

    buffer.add(e1)
    buffer.add(e2)
    buffer.add(e3)  # 此时应该把 e1 挤掉

    events = buffer.all()
    assert len(events) == 2
    assert events[0].payload["n"] == 2
    assert events[1].payload["n"] == 3


def test_memory_buffer_last():
    buffer = MemoryBuffer(max_events=5)

    for i in range(5):
        buffer.add(
            EmbryoEvent(type=EventType.HEARTBEAT, payload={"i": i + 1})
        )

    last_two = buffer.last(2)
    assert len(last_two) == 2
    assert last_two[0].payload["i"] == 4
    assert last_two[1].payload["i"] == 5
