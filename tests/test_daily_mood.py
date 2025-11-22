from __future__ import annotations

import sys
from datetime import date, datetime
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
    DailyMoodSummary,
    build_daily_mood_summary,
)


def test_daily_mood_summary_single_day(tmp_path) -> None:
    store = PerceptionStore(base_dir=tmp_path / "perception")

    # 2025-01-01 两条事件
    ts1 = datetime(2025, 1, 1, 10, 0)  # naive，直接用 date 即可
    ts2 = datetime(2025, 1, 1, 22, 0)
    # 2025-01-02 一条事件
    ts3 = datetime(2025, 1, 2, 9, 0)

    e1 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="今天很开心，也有点兴奋",
        tags=["checkin", "mood"],
        metadata={},
        timestamp=ts1,
    )
    e2 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="有点累，也有点焦虑",
        tags=["checkin", "detail"],
        metadata={},
        timestamp=ts2,
    )
    e3 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="明天的事情明天再说吧",
        tags=["checkin", "mood"],
        metadata={},
        timestamp=ts3,
    )

    store.append(e1)
    store.append(e2)
    store.append(e3)

    summary = build_daily_mood_summary(
        store,
        target_date=date(2025, 1, 1),
        channel=None,
    )

    assert isinstance(summary, DailyMoodSummary)
    assert summary.total_events == 2
    assert summary.channels_count.get(InputChannel.CLI_CHECKIN.value) == 2
    # 至少情绪统计里要有 positive / negative 某一种
    assert sum(summary.sentiment_counts.values()) == 2
    # samples 不超过 2 条
    assert 0 < len(summary.samples) <= 2


def test_daily_mood_summary_filter_channel(tmp_path) -> None:
    store = PerceptionStore(base_dir=tmp_path / "perception")

    ts = datetime(2025, 1, 1, 12, 0)

    e1 = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content="今天很开心",
        tags=["checkin"],
        metadata={},
        timestamp=ts,
    )
    e2 = PerceptionEvent.create(
        channel=InputChannel.CLI_NOTE,
        content="测试一下 daily mood 功能",
        tags=["note"],
        metadata={},
        timestamp=ts,
    )

    store.append(e1)
    store.append(e2)

    # 只看 CLI_NOTE 渠道
    summary = build_daily_mood_summary(
        store,
        target_date=date(2025, 1, 1),
        channel=InputChannel.CLI_NOTE,
    )

    assert summary.total_events == 1
    assert summary.channels_count.get(InputChannel.CLI_NOTE.value) == 1
