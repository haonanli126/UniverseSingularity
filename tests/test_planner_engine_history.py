from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner import engine as planner_engine  # type: ignore
from us_core.planner import loader as planner_loader  # type: ignore
from us_core.planner.preference_memory import TaskHistoryStats  # type: ignore


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_make_focus_block_plan_with_history_uses_preferences(monkeypatch, tmp_path: Path):
    tasks_file = tmp_path / "tasks.jsonl"
    _write_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "T1", "status": "open", "priority": 1},
            {"id": "2", "title": "T2", "status": "open", "priority": 1},
        ],
    )

    def fake_default_tasks_path():
        return tasks_file

    monkeypatch.setattr(planner_loader, "get_default_tasks_path", fake_default_tasks_path)

    # 让历史偏好强烈倾向 T2
    def fake_aggregate_task_stats():
        return {
            "1": TaskHistoryStats(task_id="1", times_planned=5, times_completed=1),
            "2": TaskHistoryStats(task_id="2", times_planned=5, times_completed=4),
        }

    monkeypatch.setattr(planner_engine, "aggregate_task_stats", fake_aggregate_task_stats)

    plan = planner_engine.make_focus_block_plan_with_history(
        mode="focus",
        max_tasks=1,
        duration_minutes=120,
    )

    assert len(plan.tasks) == 1
    assert plan.tasks[0].task.id == "2"
