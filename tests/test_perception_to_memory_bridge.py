from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import InputChannel, PerceptionEvent, PerceptionStore
from us_core.perception.memory_bridge import (
    perception_event_to_memory_item,
    build_memory_items_from_perception,
    ingest_perception_events_to_file,
)
from us_core.core.workspace import LongTermMemoryItem


def _ts() -> datetime:
    return datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_cli_checkin_becomes_emotion_memory_item() -> None:
    ev = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="今天有点累，但也挺期待的",
        tags=["checkin", "mood"],
        metadata={},
        timestamp=_ts(),
    )

    item = perception_event_to_memory_item(ev)
    assert item is not None
    assert isinstance(item, LongTermMemoryItem)
    assert item.intent_label == "emotion"
    assert "累" in item.text or "期待" in item.text


def test_dialog_user_with_strong_emotion_becomes_memory_item() -> None:
    ev = PerceptionEvent.create(
        channel=InputChannel.DIALOG,
        content="最近压力有点大，也有点焦虑。",
        tags=["dialog", "user"],
        metadata={"role": "user"},
        timestamp=_ts(),
    )

    item = perception_event_to_memory_item(ev)
    assert item is not None
    assert isinstance(item, LongTermMemoryItem)
    assert item.intent_label == "emotion"


def test_dialog_assistant_is_not_written_to_memory() -> None:
    ev = PerceptionEvent.create(
        channel=InputChannel.DIALOG,
        content="我听到了，你最近压力不小。",
        tags=["dialog", "assistant"],
        metadata={"role": "assistant"},
        timestamp=_ts(),
    )

    item = perception_event_to_memory_item(ev)
    assert item is None


def test_build_memory_items_from_perception_filters_none() -> None:
    ev1 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="今天我很开心",
        tags=["checkin", "mood"],
        metadata={},
        timestamp=_ts(),
    )
    ev2 = PerceptionEvent.create(
        channel=InputChannel.DIALOG,
        content="有点累，但也挺期待宇宙奇点的。",
        tags=["dialog", "user"],
        metadata={"role": "user"},
        timestamp=_ts(),
    )
    ev3 = PerceptionEvent.create(
        channel=InputChannel.DIALOG,
        content="这是助手的回复，不需要记成你的长期心情。",
        tags=["dialog", "assistant"],
        metadata={"role": "assistant"},
        timestamp=_ts(),
    )

    items = build_memory_items_from_perception([ev1, ev2, ev3])
    assert len(items) == 2
    assert all(isinstance(x, LongTermMemoryItem) for x in items)
    assert any("开心" in x.text for x in items)
    assert any("累" in x.text or "期待" in x.text for x in items)


def test_ingest_perception_events_to_file_writes_jsonl(tmp_path) -> None:
    base_dir = tmp_path / "perception"
    store = PerceptionStore(base_dir=base_dir)

    ev1 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="今天我很开心",
        tags=["checkin", "mood"],
        metadata={},
        timestamp=_ts(),
    )
    ev2 = PerceptionEvent.create(
        channel=InputChannel.DIALOG,
        content="有点累，但也挺期待宇宙奇点的。",
        tags=["dialog", "user"],
        metadata={"role": "user"},
        timestamp=_ts(),
    )
    ev3 = PerceptionEvent.create(
        channel=InputChannel.DIALOG,
        content="这是助手的回复，不需要记成你的长期心情。",
        tags=["dialog", "assistant"],
        metadata={"role": "assistant"},
        timestamp=_ts(),
    )

    store.append(ev1)
    store.append(ev2)
    store.append(ev3)

    out_path = tmp_path / "memory" / "perception_long_term.jsonl"
    items = ingest_perception_events_to_file(
        store,
        output_path=out_path,
        channel=None,
        limit=None,
    )

    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    assert len(lines) == len(items)

    first = json.loads(lines[0])
    assert "text" in first
    assert "intent_label" in first
    assert "timestamp" in first
