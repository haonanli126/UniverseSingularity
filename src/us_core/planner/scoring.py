from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, Tuple, Mapping, Optional

from .models import Task
from .preference_memory import TaskHistoryStats


def _priority_component(task: Task) -> float:
    if task.priority is None:
        return 0.0
    # 假设 priority 范围 1-3，适当放大
    return float(task.priority) * 1.5


def _tag_component(task: Task, mode: str) -> float:
    tags = {t.lower() for t in (task.tags or [])}
    score = 0.0

    if mode == "rest":
        if "self-care" in tags:
            score += 3.0
        if "universe" in tags or "deep-work" in tags:
            score -= 2.0
    elif mode == "focus":
        if "universe" in tags or "deep-work" in tags:
            score += 3.0
        if "self-care" in tags:
            score -= 1.0
    else:  # balance
        if "self-care" in tags:
            score += 1.0
        if "universe" in tags or "deep-work" in tags:
            score += 1.0

    return score


def _recency_component(task: Task, now: datetime) -> float:
    if task.created_at is None:
        return 0.0

    delta_days = (now - task.created_at).days
    # 越新的任务分越高，30 天以上就不再加分
    if delta_days <= 0:
        return 1.0
    if delta_days >= 30:
        return 0.0
    return max(0.0, 1.0 - delta_days / 30.0)


def _deadline_component(task: Task, now: datetime) -> float:
    """基于任务的截止时间（due_date）打分。"""
    if task.due_date is None:
        return 0.0

    delta_days = (task.due_date - now).days
    # 过期的任务给一点提醒加分，临近截止也加分
    if delta_days < 0:
        return 1.0
    if delta_days == 0:
        return 1.5
    if delta_days <= 3:
        return 1.0
    if delta_days <= 7:
        return 0.5
    return 0.0


def score_task(task: Task, mode: str, now: Optional[datetime] = None) -> Tuple[float, Dict[str, float]]:
    """基础打分函数：只考虑任务本身属性，不考虑历史表现。"""
    if now is None:
        now = datetime.now()

    components: Dict[str, float] = {}
    components["priority"] = _priority_component(task)
    components["tags"] = _tag_component(task, mode)
    components["recency"] = _recency_component(task, now)
    components["deadline"] = _deadline_component(task, now)

    total = sum(components.values())
    return total, components


def score_task_with_history(
    task: Task,
    mode: str,
    history_stats: Optional[Mapping[str, TaskHistoryStats]] = None,
    now: Optional[datetime] = None,
) -> Tuple[float, Dict[str, float]]:
    """在基础打分上，叠加「历史完成率」作为 preference 组件。

    - 若该任务从未出现在历史记录中，则 preference=0，对结果无影响；
    - 若 times_planned 较多且 completion_rate 高，则适度加分；
    - 若 times_planned 较多且 completion_rate 很低，则适度减分。
    """
    base_total, components = score_task(task, mode=mode, now=now)

    pref_score = 0.0
    if history_stats:
        stat = history_stats.get(task.id)
        if stat and stat.times_planned >= 2:
            # completion_rate ∈ [0,1]，中心 0.5
            centered = stat.completion_rate - 0.5  # ∈ [-0.5, 0.5]
            # 使用 log 放大在 2~5 次规划之间的影响，并对更多次数做饱和
            factor = math.log1p(stat.times_planned) / math.log1p(5.0)
            # 整体权重，保证 preference 大致在 [-2, 2] 区间
            weight = 4.0
            pref_score = centered * factor * weight

    components["preference"] = pref_score
    total = base_total + pref_score
    return total, components
