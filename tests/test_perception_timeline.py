from __future__ import annotations

import sys
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import (
    InputChannel,
    PerceptionEvent,
    PerceptionStore,
    TimelineSummary,
    build_timeline,
)


def _create_sample_events(store: PerceptionStore) -> None:
    e1 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="今天很开心，也有点兴奋",
        tags=["checkin", "mood"],
        metadata={},
    )
    e2 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="有点累，也有点焦虑",
        tags=["checkin", "detail"],
        metadata={},
    )
    e3 = PerceptionEvent.create(
        channel=InputChannel.CLI_NOTE,
        content="测试一下感知时间线功能，感觉不错",
        tags=["quick_note"],
        metadata={},
    )

    store.append(e1)
    store.append(e2)
    store.append(e3)


def test_build_timeline_all_channels(tmp_path) -> None:
    store = PerceptionStore(base_dir=tmp_path / "perception")
    _create_sample_events(store)

    items, summary = build_timeline(store, channel=None, limit=10)

    assert isinstance(summary, TimelineSummary)
    assert summary.total_events == 3

    # 最新的事件应该是最后 append 的那条
    assert items[0].event.content.startswith("测试一下感知时间线功能")
    # 至少有一条是正向情绪
    assert any(it.emotion.sentiment == "positive" for it in items)


def test_build_timeline_filter_by_channel(tmp_path) -> None:
    store = PerceptionStore(base_dir=tmp_path / "perception")
    _create_sample_events(store)

    items, summary = build_timeline(
        store,
        channel=InputChannel.CLI_NOTE,
        limit=10,
    )

    assert summary.total_events == 1
    assert len(items) == 1
    assert items[0].event.channel == InputChannel.CLI_NOTE
