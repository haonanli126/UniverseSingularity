from pathlib import Path
import sys
import json

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.execution_review import (  # type: ignore
    ExecutionSummary,
    parse_task_ids_from_plan_markdown,
    load_execution_for_plan,
    execution_summary_to_markdown,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_parse_task_ids_from_plan_markdown_extracts_ids():
    md = """
    ### 1. Task A

    - id: `1`
    - status: `open`

    ### 2. Task B

    - id: 2
    - status: done
    """

    ids = parse_task_ids_from_plan_markdown(md)
    assert ids == ["1", "2"]


def test_load_execution_for_plan_computes_stats(tmp_path: Path):
    tasks_file = tmp_path / "tasks.jsonl"
    _write_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "t1", "status": "done"},
            {"id": "2", "title": "t2", "status": "open"},
        ],
    )

    summary: ExecutionSummary = load_execution_for_plan(
        ["1", "2", "3"],
        tasks_path=tasks_file,
    )

    assert summary.total_planned == 3
    assert summary.found_tasks == 2
    assert summary.completed == 1
    assert summary.not_completed == 1
    assert summary.missing == 1
    assert summary.completion_rate == 0.5

    # 检查单个任务的执行标记
    item_by_id = {item.task_id: item for item in summary.items}
    assert item_by_id["1"].is_completed is True
    assert item_by_id["2"].is_completed is False
    assert item_by_id["3"].is_completed is None


def test_execution_summary_to_markdown_contains_key_stats(tmp_path: Path):
    tasks_file = tmp_path / "tasks.jsonl"
    _write_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "t1", "status": "done"},
        ],
    )

    summary = load_execution_for_plan(["1"], tasks_path=tasks_file)
    md = execution_summary_to_markdown(summary, plan_file=tmp_path / "plan.md")

    assert "Plan Execution Review" in md
    assert "completion rate" in md
    assert "t1" in md
