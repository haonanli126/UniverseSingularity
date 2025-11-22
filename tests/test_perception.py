from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import InputChannel, PerceptionEvent, PerceptionStore


def test_perception_event_create_and_roundtrip() -> None:
    ts = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    event = PerceptionEvent.create(
        channel=InputChannel.CLI_NOTE,
        content="hello universe",
        tags=["test", "note"],
        metadata={"foo": "bar"},
        timestamp=ts,
    )

    data = event.to_dict()
    restored = PerceptionEvent.from_dict(data)

    assert restored.id == event.id
    assert restored.timestamp == ts
    assert restored.channel == InputChannel.CLI_NOTE
    assert restored.content == "hello universe"
    assert restored.tags == ["test", "note"]
    assert restored.metadata["foo"] == "bar"


def test_perception_store_append_and_iter(tmp_path) -> None:
    store = PerceptionStore(base_dir=tmp_path)

    e1 = PerceptionEvent.create(
        channel=InputChannel.CLI_NOTE,
        content="first",
        tags=["t1"],
        metadata={},
    )
    e2 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="second",
        tags=["t2"],
        metadata={},
    )

    store.append(e1)
    store.append(e2)

    all_events = list(store.iter_events())
    assert len(all_events) == 2
    assert all_events[0].content == "first"
    assert all_events[1].content == "second"

    only_note = list(store.iter_events(channel=InputChannel.CLI_NOTE))
    assert len(only_note) == 1
    assert only_note[0].channel == InputChannel.CLI_NOTE

    latest = store.latest(limit=1)
    assert len(latest) == 1
    assert latest[0].content == "second"
