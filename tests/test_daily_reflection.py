from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.mood import DailyMood
from us_core.core.daily_reflection import (
    DailyReflectionContext,
    build_daily_reflection_context,
)


def _make_day(day_str: str, score: float, count: int, label: str) -> DailyMood:
    year, month, day = map(int, day_str.split("-"))
    return DailyMood(
        day=date(year, month, day),
        average_score=score,
        sample_count=count,
        label=label,
    )


def test_build_daily_reflection_context_basic() -> None:
    days = [
        _make_day("2025-01-01", -0.5, 3, "略偏负面"),
        _make_day("2025-01-02", 0.0, 2, "比较中性"),
        _make_day("2025-01-03", 0.4, 4, "略偏正面"),
    ]
    today = date(2025, 1, 3)

    ctx = build_daily_reflection_context(days, today=today, days_window=7)

    assert isinstance(ctx, DailyReflectionContext)
    assert ctx.today == today
    assert ctx.today_mood is not None
    assert ctx.today_mood.day.isoformat() == "2025-01-03"
    # 没有截断窗口，应该保留 3 天
    assert len(ctx.days_used) == 3
    # 自我照顾建议应该存在
    assert ctx.self_care is not None


def test_build_daily_reflection_context_window_trim() -> None:
    days = [
        _make_day("2025-01-01", -0.5, 3, "略偏负面"),
        _make_day("2025-01-02", -0.2, 2, "比较中性"),
        _make_day("2025-01-03", 0.1, 2, "比较中性"),
        _make_day("2025-01-04", 0.3, 3, "略偏正面"),
        _make_day("2025-01-05", 0.6, 1, "明显偏正面"),
    ]
    today = date(2025, 1, 5)

    ctx = build_daily_reflection_context(days, today=today, days_window=3)

    # 只保留最近 3 天：3、4、5
    assert len(ctx.days_used) == 3
    used_dates = [d.day.isoformat() for d in ctx.days_used]
    assert used_dates == ["2025-01-03", "2025-01-04", "2025-01-05"]

    # 今天的日情绪应该是 2025-01-05
    assert ctx.today_mood is not None
    assert ctx.today_mood.day.isoformat() == "2025-01-05"
