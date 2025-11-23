from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import json

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.execution_review import ExecutionSummary, TaskExecution  # type: ignore
from us_core.planner.preference_memory import (  # type: ignore
    append_execution_summary,
    load_history,
    aggregate_task_stats_from_records,
    attach_task_metadata,
)


def _write_tasks_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_append_execution_summary_and_aggregate_stats(tmp_path: Path):
    history_file = tmp_path / "planner_history.jsonl"

    summary = ExecutionSummary(
        total_planned=2,
        found_tasks=2,
        completed=1,
        not_completed=1,
        missing=0,
        completion_rate=0.5,
        items=[
            TaskExecution(task_id="1", title="t1", status="done", is_completed=True),
            TaskExecution(task_id="2", title="t2", status="open", is_completed=False),
        ],
    )

    append_execution_summary(
        plan_name="plan.md",
        summary=summary,
        history_path=history_file,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
    )

    records = load_history(history_file)
    assert len(records) == 3  # 2 task_execution + 1 plan_summary

    types = {rec["type"] for rec in records}
    assert "task_execution" in types
    assert "plan_summary" in types

    stats = aggregate_task_stats_from_records(records)
    assert set(stats.keys()) == {"1", "2"}
    assert stats["1"].times_planned == 1
    assert stats["1"].times_completed == 1
    assert stats["2"].times_planned == 1
    assert stats["2"].times_completed == 0
    assert stats["1"].completion_rate == 1.0
    assert stats["2"].completion_rate == 0.0


def test_attach_task_metadata_joins_titles_and_tags(tmp_path: Path):
    # 构造简单的 stats
    class SimpleStats:
        def __init__(self, task_id: str, planned: int, completed: int):
            self.task_id = task_id
            self.times_planned = planned
            self.times_completed = completed

        @property
        def completion_rate(self) -> float:
            if self.times_planned == 0:
                return 0.0
            return self.times_completed / self.times_planned

    stats = {
        "1": SimpleStats("1", planned=3, completed=2),
        "2": SimpleStats("2", planned=2, completed=1),
    }

    tasks_file = tmp_path / "tasks.jsonl"
    _write_tasks_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "T1", "status": "open", "tags": ["universe"]},
            {"id": "2", "title": "T2", "status": "open", "tags": ["self-care"]},
        ],
    )

    enriched = attach_task_metadata(stats, tasks_path=tasks_file)
    by_id = {e["task_id"]: e for e in enriched}

    assert by_id["1"]["title"] == "T1"
    assert by_id["1"]["tags"] == ["universe"]
    assert by_id["1"]["times_planned"] == 3
    assert by_id["1"]["times_completed"] == 2
    assert by_id["2"]["title"] == "T2"
    assert by_id["2"]["tags"] == ["self-care"]
