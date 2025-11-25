from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.circulation.buffers import ActionQueue, MessageBus, PerceptionBuffer  # noqa: E402


def test_perception_buffer_fifo():
    buf = PerceptionBuffer(maxlen=3)
    buf.push(1)
    buf.push(2)
    buf.push(3)
    assert len(buf) == 3

    items = buf.pop_all()
    assert items == [1, 2, 3]
    assert len(buf) == 0


def test_action_queue_priority_order():
    q = ActionQueue()
    q.push("low", priority=5)
    q.push("high", priority=0)
    q.push("mid", priority=3)

    first, _ = q.pop_next()
    second, _ = q.pop_next()
    third, _ = q.pop_next()
    assert first == "high"
    assert second == "mid"
    assert third == "low"
    assert q.pop_next() is None


def test_message_bus_publish_and_get():
    bus = MessageBus()
    bus.publish("topic1", {"a": 1})
    bus.publish("topic1", {"b": 2})
    bus.publish("topic2", {"c": 3})

    msgs1 = bus.get_messages("topic1")
    assert len(msgs1) == 2
    assert bus.get_messages("topic1") == []  # cleared

    msgs2 = bus.get_messages("topic2", clear=False)
    assert len(msgs2) == 1
    # 再次获取，仍然存在
    assert len(bus.get_messages("topic2", clear=False)) == 1
