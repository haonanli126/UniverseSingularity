from __future__ import annotations

"""
任务存储与基础编辑工具（Phase 3-S07）

作用：
- 统一读写 data/tasks/tasks.jsonl
- 提供按 id 查找、更新 title / priority / status 的基础操作
- 提供为任务添加 / 移除标签（tags）的能力
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


def add_tag_to_task(
    tasks: List[JsonDict],
    task_id: str,
    tag: str,
) -> bool:
    """
    为任务添加一个标签（tag）：

    - 如果任务不存在 -> 返回 False
    - 如果任务存在：
        - 没有 tags 字段      -> 创建为 [tag]
        - tags 是列表        -> 如果不存在则 append
        - tags 是其他类型    -> 尝试转为 [str(tags), tag]
      最终返回 True（表示找到该任务并尝试更新）
    """
    idx = find_task_index(tasks, task_id)
    if idx is None:
        return False

    t = tasks[idx]
    raw = t.get("tags")

    normalized: List[str]
    if raw is None:
        normalized = []
    elif isinstance(raw, list):
        # 将所有元素转成 str，避免意外类型
        normalized = [str(x) for x in raw]
    else:
        # 如果原来是字符串/其他，则统一包进列表
        normalized = [str(raw)]

    tag_str = str(tag).strip()
    if tag_str and tag_str not in normalized:
        normalized.append(tag_str)

    t["tags"] = normalized
    return True


def remove_tag_from_task(
    tasks: List[JsonDict],
    task_id: str,
    tag: str,
) -> bool:
    """
    从任务中移除一个标签（tag）：

    - 如果任务不存在 -> 返回 False
    - 如果任务存在：
        - 如果 tags 不是列表，则不做任何修改，但返回 True
        - 否则过滤掉等于 tag 的元素，并写回列表
      返回值只表示“是否找到任务”，不保证 tag 一定存在。
    """
    idx = find_task_index(tasks, task_id)
    if idx is None:
        return False

    t = tasks[idx]
    raw = t.get("tags")
    if not isinstance(raw, list):
        # 没有规范的 tags 列表，不做修改
        return True

    tag_str = str(tag).strip()
    filtered = [str(x) for x in raw if str(x) != tag_str]
    t["tags"] = filtered
    return True
