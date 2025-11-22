from __future__ import annotations

"""
任务推荐模块（Phase 3-S04）

作用：
- 根据 SelfCareSuggestion（rest/balance/focus），决定今天建议做多少个任务
- 在给定任务列表中，过滤出「还没完成」的任务
- 按优先级排序后，选出前 N 个作为「今日推荐任务」
"""

from typing import Any, Dict, Iterable, List, Sequence

from .self_care import SelfCareSuggestion


def recommend_task_count(suggestion: SelfCareSuggestion) -> int:
    """
    根据自我照顾模式，给出一个「建议任务数量」的基准值：

    - rest    -> 2（更少任务，优先减负）
    - balance -> 4（适中，既照顾自己也有推进）
    - focus   -> 6（状态不错，可以多做一点）

    实际使用时仍然会和 open 任务数量取 min。
    """
    mode = suggestion.mode

    if mode == "rest":
        base = 2
    elif mode == "balance":
        base = 4
    else:
        # 包括 "focus" 以及未来可能新增的模式
        base = 6

    # 至少保持 1 个，避免出现 0 个任务的尴尬情况
    return max(1, base)


def _is_open(task: Dict[str, Any]) -> bool:
    """
    判断任务是否「未完成」：

    - 如果没有 status 字段，默认视为 open
    - 如果有 status，则只要不是 "done"/"completed" 就视作未完成
    """
    status = str(task.get("status") or "").lower().strip()
    if not status:
        return True
    return status not in {"done", "completed", "closed"}


def _priority_value(task: Dict[str, Any]) -> int:
    """
    计算任务的优先级数值：

    - 优先使用整数 priority 字段
    - 如果不存在或非法，则视为 0
    """
    value = task.get("priority", 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def filter_open_tasks(tasks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    从任务列表中过滤出还没完成的任务，保持原有字段不变。
    """
    return [t for t in tasks if _is_open(t)]


def recommend_tasks_for_today(
    tasks: Sequence[Dict[str, Any]],
    suggestion: SelfCareSuggestion,
) -> List[Dict[str, Any]]:
    """
    在一组任务中，根据自我照顾建议挑出「今日推荐任务」。

    规则：
      1. 只考虑「未完成」任务（_is_open == True）
      2. 按 priority 从高到低排序（缺省为 0）
      3. 取前 recommend_task_count(suggestion) 个任务
    """
    open_tasks = filter_open_tasks(tasks)
    if not open_tasks:
        return []

    # 按 priority 从高到低排序；如果相同，则保持原有相对顺序
    sorted_tasks = sorted(
        open_tasks,
        key=_priority_value,
        reverse=True,
    )

    max_count = recommend_task_count(suggestion)
    max_count = min(max_count, len(sorted_tasks))
    return sorted_tasks[:max_count]
