from __future__ import annotations

import sys
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.task_store import (
    load_tasks,
    save_tasks,
    find_task_index,
    update_task_title,
    update_task_priority,
    update_task_status,
)


def test_load_and_save_tasks_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "tasks.jsonl"
    original = [
        {"id": "1", "title": "task-1", "priority": 0, "status": "open"},
        {"id": "2", "title": "task-2", "priority": 5, "status": "done"},
    ]

    save_tasks(path, original)
    loaded = load_tasks(path)

    assert loaded == original


def test_find_task_index_by_id() -> None:
    tasks = [
        {"id": "1", "title": "A"},
        {"task_id": "legacy-2", "title": "B"},
        {"id": "3", "title": "C"},
    ]

    assert find_task_index(tasks, "1") == 0
    assert find_task_index(tasks, "legacy-2") == 1
    assert find_task_index(tasks, "not-exist") is None


def test_update_title_priority_status() -> None:
    tasks = [
        {"id": "1", "title": "old", "priority": 0, "status": "open"},
        {"id": "2", "title": "keep", "priority": 1, "status": "open"},
    ]

    assert update_task_title(tasks, "1", "new-title")
    assert tasks[0]["title"] == "new-title"

    assert update_task_priority(tasks, "1", 10)
    assert tasks[0]["priority"] == 10

    assert update_task_status(tasks, "1", "done")
    assert tasks[0]["status"] == "done"

    # 不存在的 id 返回 False，且不修改任何任务
    assert not update_task_title(tasks, "999", "x")
    assert not update_task_priority(tasks, "999", 1)
    assert not update_task_status(tasks, "999", "open")
