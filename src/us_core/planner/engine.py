from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Iterable, List, Optional

from .filters import filter_tasks
from .loader import iter_open_tasks, load_tasks_from_jsonl
from .models import FilterSpec, PlanConfig, PlanResult, PlannedTask, Task
from .scoring import score_task, score_task_with_history
from .preference_memory import aggregate_task_stats, TaskHistoryStats


def _sorted_scored_tasks(tasks: Iterable[Task], mode: str) -> List[PlannedTask]:
    """按模式对一组任务打分并排序（从高到低），不考虑历史表现。"""
    scored: List[PlannedTask] = []
    now = datetime.now()
    for t in tasks:
        score, components = score_task(t, mode=mode, now=now)
        scored.append(PlannedTask(task=t, score=score, reasons=components))

    scored.sort(
        key=lambda pt: (
            pt.score,
            (pt.task.priority or 0),
            pt.task.created_at or 0,
        ),
        reverse=True,
    )
    return scored


def _sorted_scored_tasks_with_history(
    tasks: Iterable[Task],
    mode: str,
    history_stats: Optional[dict[str, TaskHistoryStats]] = None,
) -> List[PlannedTask]:
    """按模式对一组任务打分并排序（从高到低），叠加历史偏好。"""
    scored: List[PlannedTask] = []
    now = datetime.now()
    for t in tasks:
        score, components = score_task_with_history(t, mode=mode, history_stats=history_stats, now=now)
        scored.append(PlannedTask(task=t, score=score, reasons=components))

    scored.sort(
        key=lambda pt: (
            pt.score,
            (pt.task.priority or 0),
            pt.task.created_at or 0,
        ),
        reverse=True,
    )
    return scored


def make_focus_block_plan(
    mode: str,
    max_tasks: int = 5,
    duration_minutes: int = 90,
    filter_spec: Optional[FilterSpec] = None,
) -> PlanResult:
    """基础版：不考虑历史偏好的 focus block 计划。"""
    tasks = load_tasks_from_jsonl()
    open_tasks = list(iter_open_tasks(tasks))

    if filter_spec is None:
        filter_spec = FilterSpec()

    filtered = filter_tasks(open_tasks, filter_spec)
    if not filtered:
        return PlanResult(mode=mode, total_estimated_minutes=0, tasks=[])

    scored = _sorted_scored_tasks(filtered, mode=mode)

    selected: List[PlannedTask] = []
    total_minutes = 0

    for planned in scored:
        est = planned.task.estimated_minutes or 25

        if selected and total_minutes + est > duration_minutes:
            continue

        selected.append(planned)
        total_minutes += est

        if len(selected) >= max_tasks:
            break

    return PlanResult(mode=mode, total_estimated_minutes=total_minutes, tasks=selected)


def make_focus_block_plan_with_history(
    mode: str,
    max_tasks: int = 5,
    duration_minutes: int = 90,
    filter_spec: Optional[FilterSpec] = None,
) -> PlanResult:
    """带历史偏好的 focus block 计划。

    - 当 planner_history.jsonl 不存在或没有相关记录时，行为会退化为基础版；
    - 当某些任务历史完成率很低 / 很高时，会对其得分做适度调整。
    """
    tasks = load_tasks_from_jsonl()
    open_tasks = list(iter_open_tasks(tasks))

    if filter_spec is None:
        filter_spec = FilterSpec()

    filtered = filter_tasks(open_tasks, filter_spec)
    if not filtered:
        return PlanResult(mode=mode, total_estimated_minutes=0, tasks=[])

    # 加载历史偏好统计
    history_stats = aggregate_task_stats()

    scored = _sorted_scored_tasks_with_history(filtered, mode=mode, history_stats=history_stats or None)

    selected: List[PlannedTask] = []
    total_minutes = 0

    for planned in scored:
        est = planned.task.estimated_minutes or 25

        if selected and total_minutes + est > duration_minutes:
            continue

        selected.append(planned)
        total_minutes += est

        if len(selected) >= max_tasks:
            break

    return PlanResult(mode=mode, total_estimated_minutes=total_minutes, tasks=selected)


def plan_to_markdown(plan: PlanResult) -> str:
    lines: List[str] = []
    lines.append(f"## Focus Block Plan ({plan.mode})")
    lines.append("")
    lines.append(f"- total_estimated_minutes: **{plan.total_estimated_minutes}**")
    lines.append(f"- task_count: **{len(plan.tasks)}**")
    lines.append("")

    if not plan.tasks:
        lines.append("> 当前没有可用任务生成计划。")
        return "\n".join(lines)

    for idx, planned in enumerate(plan.tasks, start=1):
        t = planned.task
        est = t.estimated_minutes or 25
        tags = ", ".join(t.tags) if t.tags else "-"
        reasons = ", ".join(f"{k}: {v:+.2f}" for k, v in planned.reasons.items() if abs(v) > 0.01)

        lines.append(f"### {idx}. {t.title}")
        lines.append("")
        lines.append(f"- id: `{t.id}`")
        lines.append(f"- status: `{t.status}`")
        lines.append(f"- priority: `{t.priority}`")
        lines.append(f"- estimated_minutes: `{est}`")
        lines.append(f"- tags: {tags}")
        lines.append(f"- score: **{planned.score:.2f}**")
        lines.append(f"- reasons: {reasons or '-'}")
        lines.append("")

    return "\n".join(lines)


def plan_to_dict(plan: PlanResult) -> dict:
    return {
        "mode": plan.mode,
        "total_estimated_minutes": plan.total_estimated_minutes,
        "tasks": [asdict(pt.task) for pt in plan.tasks],
    }

