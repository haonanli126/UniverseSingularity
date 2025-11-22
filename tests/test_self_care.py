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
from us_core.core.self_care import (
    SelfCareSuggestion,
    build_self_care_suggestion,
)


def _make_day(day_str: str, score: float, count: int, label: str) -> DailyMood:
    year, month, day = map(int, day_str.split("-"))
    return DailyMood(
        day=date(year, month, day),
        average_score=score,
        sample_count=count,
        label=label,
    )


def test_build_self_care_suggestion_rest_mode() -> None:
    days = [
        _make_day("2025-01-01", -0.8, 3, "明显偏负面"),
        _make_day("2025-01-02", -0.5, 2, "略偏负面"),
    ]
    suggestion = build_self_care_suggestion(days)
    assert isinstance(suggestion, SelfCareSuggestion)
    assert suggestion.mode == "rest"
    assert suggestion.average_mood <= -0.4
    assert "压力不小" in suggestion.message or "放点水" in suggestion.message


def test_build_self_care_suggestion_balance_mode() -> None:
    days = [
        _make_day("2025-01-01", -0.1, 3, "比较中性"),
        _make_day("2025-01-02", 0.0, 2, "比较中性"),
        _make_day("2025-01-03", 0.1, 2, "比较中性"),
    ]
    suggestion = build_self_care_suggestion(days)
    assert isinstance(suggestion, SelfCareSuggestion)
    assert suggestion.mode == "balance"
    assert -0.4 < suggestion.average_mood < 0.2
    assert "平衡" in suggestion.message or "起伏" in suggestion.message


def test_build_self_care_suggestion_focus_mode() -> None:
    days = [
        _make_day("2025-01-01", 0.3, 3, "略偏正面"),
        _make_day("2025-01-02", 0.6, 2, "明显偏正面"),
    ]
    suggestion = build_self_care_suggestion(days)
    assert isinstance(suggestion, SelfCareSuggestion)
    assert suggestion.mode == "focus"
    assert suggestion.average_mood >= 0.2
    assert "状态整体还不错" in suggestion.message or "挑战" in suggestion.message
