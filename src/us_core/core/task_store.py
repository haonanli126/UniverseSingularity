from __future__ import annotations

"""
任务存储与基础编辑工具（Phase 3-S05）

作用：
- 统一读写 data/tasks/tasks.jsonl
- 提供按 id 查找、更新 title / priority / status 的基础操作
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

JsonDict = Dict[str, Any]


def load_tasks(path: Path) -> List[JsonDict]:
    """
    从 JSONL 文件加载任务列表。
    - 每行一个 JSON 对象，必须是 dict 才会被接受。
    - 对于不存在的文件，返回空列表。
    """
    tasks: List[JsonDict] = []
    if not path.exists():
        return tasks

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                tasks.append(obj)

    return tasks


def save_tasks(path: Path, tasks: List[JsonDict]) -> None:
    """
    将任务列表写回 JSONL 文件。
    - 覆盖写入
    - 保留所有字段，只要是 dict 内容就原样 dump
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for task in tasks:
            json.dump(task, f, ensure_ascii=False)
            f.write("\n")


def find_task_index(tasks: List[JsonDict], task_id: str) -> Optional[int]:
    """
    在任务列表中根据 id / task_id 查找任务下标。
    - 优先使用 "id"
    - 其次尝试 "task_id"
    - 都没有则视作找不到
    """
    target = str(task_id)
    for idx, task in enumerate(tasks):
        tid = task.get("id") or task.get("task_id")
        if tid is None:
            continue
        if str(tid) == target:
            return idx
    return None


def update_task_title(
    tasks: List[JsonDict],
    task_id: str,
    new_title: str,
) -> bool:
    """
    更新某个任务的 title。
    返回：
      - True  表示找到并更新成功
      - False 表示未找到对应任务
    """
    idx = find_task_index(tasks, task_id)
    if idx is None:
        return False

    tasks[idx]["title"] = str(new_title).strip()
    return True


def update_task_priority(
    tasks: List[JsonDict],
    task_id: str,
    new_priority: int,
) -> bool:
    """
    更新某个任务的 priority（整数）。
    """
    idx = find_task_index(tasks, task_id)
    if idx is None:
        return False

    try:
        value = int(new_priority)
    except (TypeError, ValueError):
        value = 0

    tasks[idx]["priority"] = value
    return True


def update_task_status(
    tasks: List[JsonDict],
    task_id: str,
    new_status: str,
) -> bool:
    """
    更新某个任务的 status。
    - 不强制状态值，只是写入字符串（如: "open" / "in_progress" / "done"）
    """
    idx = find_task_index(tasks, task_id)
    if idx is None:
        return False

    tasks[idx]["status"] = str(new_status).strip()
    return True
