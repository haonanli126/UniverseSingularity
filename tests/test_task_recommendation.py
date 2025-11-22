from __future__ import annotations

import sys
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.self_care import SelfCareSuggestion
from us_core.core.task_recommendation import (
    filter_open_tasks,
    recommend_task_count,
    recommend_tasks_for_today,
)


def _make_suggestion(mode: str, avg: float = 0.0, days: int = 3) -> SelfCareSuggestion:
    return SelfCareSuggestion(
        mode=mode,
        message=f"mode={mode}",
        average_mood=avg,
        days_considered=days,
    )


def test_recommend_task_count_by_mode() -> None:
    s_rest = _make_suggestion("rest")
    s_balance = _make_suggestion("balance")
    s_focus = _make_suggestion("focus")

    assert recommend_task_count(s_rest) == 2
    assert recommend_task_count(s_balance) == 4
    assert recommend_task_count(s_focus) == 6

    # 即便是未知模式，也应该走 "focus" 的兜底逻辑
    s_other = _make_suggestion("unknown")
    assert recommend_task_count(s_other) >= 1


def test_filter_open_tasks_filters_completed() -> None:
    tasks = [
        {"id": "1", "title": "open-1"},
        {"id": "2", "title": "open-2", "status": "open"},
        {"id": "3", "title": "done-1", "status": "done"},
        {"id": "4", "title": "done-2", "status": "completed"},
    ]
    open_tasks = filter_open_tasks(tasks)
    ids = [t["id"] for t in open_tasks]
    assert ids == ["1", "2"]


def test_recommend_tasks_for_today_respects_priority_and_mode() -> None:
    tasks = [
        {"id": "1", "title": "low-priority", "priority": 0},
        {"id": "2", "title": "mid-priority", "priority": 5},
        {"id": "3", "title": "high-priority", "priority": 10},
        {"id": "4", "title": "done-task", "priority": 100, "status": "done"},
    ]

    # rest 模式：最多 2 个任务
    s_rest = _make_suggestion("rest")
    rec_rest = recommend_tasks_for_today(tasks, s_rest)
    assert [t["id"] for t in rec_rest] == ["3", "2"]

    # focus 模式：最多 3 个任务（因为 open 只有 3 个）
    s_focus = _make_suggestion("focus")
    rec_focus = recommend_tasks_for_today(tasks, s_focus)
    assert [t["id"] for t in rec_focus] == ["3", "2", "1"]
