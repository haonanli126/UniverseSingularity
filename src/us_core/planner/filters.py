from __future__ import annotations

from typing import Iterable, List

from .models import FilterSpec, Task


def filter_tasks(tasks: Iterable[Task], spec: FilterSpec) -> List[Task]:
    """按 FilterSpec 对任务进行过滤。"""
    result: List[Task] = []
    search_lower = spec.search.lower() if spec.search else None

    for task in tasks:
        if spec.statuses is not None:
            if task.status.lower() not in {s.lower() for s in spec.statuses}:
                continue

        if spec.min_priority is not None and task.priority is not None:
            if task.priority < spec.min_priority:
                continue

        if spec.max_priority is not None and task.priority is not None:
            if task.priority > spec.max_priority:
                continue

        if spec.include_tags is not None:
            # 只要有一个 tag 命中就算包含
            task_tags_lower = {t.lower() for t in task.tags}
            if not any(tag.lower() in task_tags_lower for tag in spec.include_tags):
                continue

        if spec.exclude_tags is not None:
            task_tags_lower = {t.lower() for t in task.tags}
            if any(tag.lower() in task_tags_lower for tag in spec.exclude_tags):
                continue

        if search_lower:
            text = (task.title + " " + " ".join(task.tags)).lower()
            if search_lower not in text:
                continue

        result.append(task)

    return result
