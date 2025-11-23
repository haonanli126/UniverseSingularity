from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .models import Task


def get_default_tasks_path() -> Path:
    """
    默认的 tasks.jsonl 路径：项目根目录 / data/tasks/tasks.jsonl

    假设当前文件在 src/us_core/planner/loader.py
    parents:
      [0] = planner
      [1] = us_core
      [2] = src
      [3] = project root
    """
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "data" / "tasks" / "tasks.jsonl"


def load_tasks_from_jsonl(path: Path | None = None) -> List[Task]:
    """
    从 JSONL 文件加载任务。遇到坏行会跳过，不会抛异常。

    :param path: 可选自定义路径，不传就用默认路径。
    """
    if path is None:
        path = get_default_tasks_path()

    if not path.exists():
        return []

    tasks: List[Task] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                # 坏行直接跳过
                continue

            if not isinstance(data, dict):
                continue

            try:
                task = Task.from_dict(data)
            except Exception:
                # 单个任务出问题也跳过，保证整体健壮
                continue
            tasks.append(task)
    return tasks


def iter_open_tasks(tasks: Iterable[Task]) -> Iterable[Task]:
    """只保留尚未完成的任务。status 简单按字符串匹配。"""
    done_statuses = {"done", "completed", "cancelled", "canceled", "archived"}
    for t in tasks:
        if t.status.lower() in done_statuses:
            continue
        yield t
