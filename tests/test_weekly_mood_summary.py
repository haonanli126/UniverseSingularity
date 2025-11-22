from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.mood import DailyMood
from us_core.core.mood_summary import (
    WeeklyMoodSummary,
    summarize_weekly_mood,
    generate_weekly_mood_summary_text,
)


def _make_day(day_str: str, score: float, count: int, label: str) -> DailyMood:
    year, month, day = map(int, day_str.split("-"))
    return DailyMood(
        day=date(year, month, day),
        average_score=score,
        sample_count=count,
        label=label,
    )


def test_summarize_weekly_mood_basic() -> None:
    days = [
        _make_day("2025-01-01", -0.8, 3, "略偏负面"),
        _make_day("2025-01-02", -0.2, 2, "比较中性"),
        _make_day("2025-01-03", 0.4, 4, "略偏正面"),
    ]

    summary = summarize_weekly_mood(days)

    assert isinstance(summary, WeeklyMoodSummary)
    assert len(summary.days) == 3
    # 2025-01-03 应该是最好的一天
    assert summary.best_day.day.isoformat() == "2025-01-03"
    # 2025-01-01 应该是最难的一天
    assert summary.worst_day.day.isoformat() == "2025-01-01"
    # 整体平均分应该在 [-0.2, 0.0] 之间
    assert -0.2 <= summary.overall_average <= 0.0


def test_generate_weekly_mood_summary_text_contains_key_phrases() -> None:
    days = [
        _make_day("2025-01-01", -0.8, 3, "略偏负面"),
        _make_day("2025-01-02", -0.2, 2, "比较中性"),
        _make_day("2025-01-03", 0.4, 4, "略偏正面"),
    ]

    summary = summarize_weekly_mood(days)
    text = generate_weekly_mood_summary_text(summary)

    assert "从 2025-01-01 到 2025-01-03" in text
    assert "整体情绪可以形容为" in text
    assert "情绪相对最好的一天" in text
    assert "情绪最吃力的一天" in text
    assert "无论这几天是偏轻松还是偏辛苦" in text
