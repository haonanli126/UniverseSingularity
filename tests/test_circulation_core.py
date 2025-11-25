from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.circulation.core import CirculationSystem  # noqa: E402
from us_core.systems.circulation.api_client import ModelApiClient  # noqa: E402


def test_circulation_ingest_and_drain_perceptions():
    system = CirculationSystem()
    p1 = {"type": "event", "value": 1}
    p2 = {"type": "event", "value": 2}

    system.ingest_perception(p1)
    system.ingest_perception(p2)

    drained = system.drain_perceptions()
    assert drained == [p1, p2]
    assert system.drain_perceptions() == []


def test_circulation_queue_actions_and_order():
    system = CirculationSystem()
    system.queue_action({"name": "low"}, priority=5)
    system.queue_action({"name": "high"}, priority=0)

    actions = system.get_actions_to_execute()
    assert [a["name"] for a in actions] == ["high", "low"]


def test_circulation_ask_model_uses_client():
    calls: List[Dict] = []

    def fake_call(model: str, messages):
        calls.append({"model": model, "messages": messages})
        return "ok"

    client = ModelApiClient(model="gpt-4.1", call_fn=fake_call)
    system = CirculationSystem(model_client=client)

    messages = [{"role": "user", "content": "hi"}]
    result = system.ask_model(messages)

    assert result == "ok"
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-4.1"
    assert calls[0]["messages"] == messages


def test_circulation_ask_model_without_client_returns_none():
    system = CirculationSystem(model_client=None)
    assert system.ask_model([{"role": "user", "content": "hi"}]) is None
