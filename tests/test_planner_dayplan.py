from pathlib import Path
import sys
import json

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.dayplan import DayBlockSpec, build_day_plan  # type: ignore
from us_core.planner.models import FilterSpec  # type: ignore
from us_core.planner import loader as planner_loader  # type: ignore


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def test_build_day_plan_distributes_tasks_without_duplicates(monkeypatch, tmp_path):
    # 构造简单的 tasks.jsonl
    tasks_file = tmp_path / "tasks.jsonl"
    _write_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "self care 1", "status": "open", "tags": ["self-care"], "priority": 1},
            {"id": "2", "title": "universe 1", "status": "open", "tags": ["universe"], "priority": 3},
            {"id": "3", "title": "universe 2", "status": "open", "tags": ["universe"], "priority": 2},
        ],
    )

    def fake_default_tasks_path():
        return tasks_file

    monkeypatch.setattr(planner_loader, "get_default_tasks_path", fake_default_tasks_path)

    block_specs = [
        DayBlockSpec(name="morning", mode="focus", duration_minutes=120, max_tasks=2),
        DayBlockSpec(name="evening", mode="rest", duration_minutes=120, max_tasks=2),
    ]

    day_plan = build_day_plan(base_mode="focus", block_specs=block_specs)

    # 每个任务至多在一个 block 里出现
    all_ids = []
    for block in day_plan.blocks:
        all_ids.extend([pt.task.id for pt in block.plan.tasks])

    assert len(all_ids) == len(set(all_ids))


def test_build_day_plan_respects_filter_spec(monkeypatch, tmp_path):
    tasks_file = tmp_path / "tasks.jsonl"
    _write_jsonl(
        tasks_file,
        [
            {"id": "1", "title": "self care 1", "status": "open", "tags": ["self-care"], "priority": 1},
            {"id": "2", "title": "universe 1", "status": "open", "tags": ["universe"], "priority": 3},
        ],
    )

    def fake_default_tasks_path():
        return tasks_file

    monkeypatch.setattr(planner_loader, "get_default_tasks_path", fake_default_tasks_path)

    block_specs = [
        DayBlockSpec(name="morning", mode="focus", duration_minutes=120, max_tasks=3),
        DayBlockSpec(name="evening", mode="rest", duration_minutes=120, max_tasks=3),
    ]

    # 只允许 universe 标签
    filter_spec = FilterSpec(include_tags={"universe"})

    day_plan = build_day_plan(base_mode="focus", block_specs=block_specs, filter_spec=filter_spec)

    for block in day_plan.blocks:
        for pt in block.plan.tasks:
            assert "universe" in [t.lower() for t in pt.task.tags]


def test_build_day_plan_returns_empty_when_no_tasks(monkeypatch, tmp_path):
    tasks_file = tmp_path / "empty.jsonl"
    tasks_file.write_text("", encoding="utf-8")

    def fake_default_tasks_path():
        return tasks_file

    monkeypatch.setattr(planner_loader, "get_default_tasks_path", fake_default_tasks_path)

    block_specs = [
        DayBlockSpec(name="morning", mode="focus", duration_minutes=90, max_tasks=3),
        DayBlockSpec(name="afternoon", mode="balance", duration_minutes=90, max_tasks=3),
    ]

    day_plan = build_day_plan(base_mode="balance", block_specs=block_specs)

    assert day_plan.blocks == []
