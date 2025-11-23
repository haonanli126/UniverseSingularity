from pathlib import Path
import sys

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.engine import make_focus_block_plan
from us_core.planner.loader import load_tasks_from_jsonl
from us_core.planner.models import Task


def _write_jsonl(path: Path, lines: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        import json

        for obj in lines:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_load_tasks_from_jsonl_with_simple_file(tmp_path):
    file_path = tmp_path / "tasks.jsonl"
    _write_jsonl(
        file_path,
        [
            {"id": "1", "title": "t1", "status": "open", "priority": 1, "tags": ["self-care"]},
            {"id": "2", "title": "t2", "status": "done", "priority": 3, "tags": ["universe"]},
        ],
    )

    tasks = load_tasks_from_jsonl(file_path)
    assert len(tasks) == 2
    assert tasks[0].id == "1"
    assert tasks[0].title == "t1"
    assert tasks[0].tags == ["self-care"]


def test_make_focus_block_plan_respects_mode_and_max_tasks(monkeypatch, tmp_path):
    # 在一个临时目录下构造假的 tasks.jsonl，
    # 然后 monkeypatch loader.get_default_tasks_path 让引擎去读这份文件
    from us_core.planner import loader

    tasks_file = tmp_path / "tasks.jsonl"
    _write_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "self care 1", "status": "open", "tags": ["self-care"], "priority": 1},
            {"id": "2", "title": "self care 2", "status": "open", "tags": ["self-care"], "priority": 2},
            {"id": "3", "title": "universe work", "status": "open", "tags": ["universe"], "priority": 3},
        ],
    )

    def fake_default_tasks_path():
        return tasks_file

    monkeypatch.setattr(loader, "get_default_tasks_path", fake_default_tasks_path)

    # rest 模式：倾向 self-care
    plan_rest = make_focus_block_plan(mode="rest", max_tasks=2, duration_minutes=120)
    ids_rest = [pt.task.id for pt in plan_rest.tasks]
    assert "3" not in ids_rest  # universe 任务应当被压制

    # focus 模式：universe 任务应该进入前几名
    plan_focus = make_focus_block_plan(mode="focus", max_tasks=2, duration_minutes=120)
    ids_focus = [pt.task.id for pt in plan_focus.tasks]
    assert "3" in ids_focus


def test_make_focus_block_plan_returns_empty_when_no_tasks(monkeypatch, tmp_path):
    from us_core.planner import loader

    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")

    def fake_default_tasks_path():
        return empty_file

    monkeypatch.setattr(loader, "get_default_tasks_path", fake_default_tasks_path)

    plan = make_focus_block_plan(mode="balance")
    assert plan.tasks == []
    assert plan.total_estimated_minutes == 0
