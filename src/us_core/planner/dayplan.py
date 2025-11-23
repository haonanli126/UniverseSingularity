from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .filters import filter_tasks
from .loader import iter_open_tasks, load_tasks_from_jsonl
from .models import FilterSpec, PlanResult, PlannedTask, Task
from .scoring import score_task, score_task_with_history
from .preference_memory import aggregate_task_stats, TaskHistoryStats


@dataclass
class DayBlockSpec:
    """一天中的一个 Block 配置。"""

    name: str  # e.g. "morning", "afternoon", "evening"
    mode: str  # "rest" / "balance" / "focus"
    duration_minutes: int = 90
    max_tasks: int = 5
    default_task_minutes: int = 25


@dataclass
class DayBlockPlan:
    spec: DayBlockSpec
    plan: PlanResult


@dataclass
class DayPlanResult:
    base_mode: str
    blocks: List[DayBlockPlan]

    @property
    def total_estimated_minutes(self) -> int:
        return sum(b.plan.total_estimated_minutes for b in self.blocks)


def _sorted_scored_tasks(tasks: Iterable[Task], mode: str) -> List[PlannedTask]:
    """不考虑历史偏好，按模式打分排序。"""
    from datetime import datetime

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
    """考虑历史偏好的版本。"""
    from datetime import datetime

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


def _make_block_plan(
    tasks: List[Task],
    spec: DayBlockSpec,
) -> PlanResult:
    """基础版 block 规划，不考虑历史偏好。"""
    scored = _sorted_scored_tasks(tasks, spec.mode)

    selected: List[PlannedTask] = []
    total_minutes = 0

    for planned in scored:
        est = planned.task.estimated_minutes or spec.default_task_minutes

        if selected and total_minutes + est > spec.duration_minutes:
            continue

        selected.append(planned)
        total_minutes += est

        if len(selected) >= spec.max_tasks:
            break

    return PlanResult(mode=spec.mode, total_estimated_minutes=total_minutes, tasks=selected)


def _make_block_plan_with_history(
    tasks: List[Task],
    spec: DayBlockSpec,
    history_stats: Optional[dict[str, TaskHistoryStats]] = None,
) -> PlanResult:
    """带历史偏好的 block 规划。"""
    scored = _sorted_scored_tasks_with_history(tasks, spec.mode, history_stats=history_stats)

    selected: List[PlannedTask] = []
    total_minutes = 0

    for planned in scored:
        est = planned.task.estimated_minutes or spec.default_task_minutes

        if selected and total_minutes + est > spec.duration_minutes:
            continue

        selected.append(planned)
        total_minutes += est

        if len(selected) >= spec.max_tasks:
            break

    return PlanResult(mode=spec.mode, total_estimated_minutes=total_minutes, tasks=selected)


def build_day_plan(
    base_mode: str,
    block_specs: List[DayBlockSpec],
    *,
    filter_spec: Optional[FilterSpec] = None,
) -> DayPlanResult:
    """基础版：不考虑历史偏好的一天多 block 计划。"""
    base_mode = (base_mode or "balance").strip().lower()
    if base_mode not in {"rest", "balance", "focus"}:
        base_mode = "balance"

    raw_tasks = load_tasks_from_jsonl()
    if not raw_tasks:
        return DayPlanResult(base_mode=base_mode, blocks=[])

    open_tasks = list(iter_open_tasks(raw_tasks))

    if filter_spec is None:
        filter_spec = FilterSpec()

    remaining_tasks = filter_tasks(open_tasks, filter_spec)

    if not remaining_tasks:
        return DayPlanResult(base_mode=base_mode, blocks=[])

    blocks: List[DayBlockPlan] = []

    for spec in block_specs:
        if not remaining_tasks:
            blocks.append(DayBlockPlan(spec=spec, plan=PlanResult(mode=spec.mode, total_estimated_minutes=0, tasks=[])))
            continue

        plan = _make_block_plan(remaining_tasks, spec)
        blocks.append(DayBlockPlan(spec=spec, plan=plan))

        used_ids = {pt.task.id for pt in plan.tasks}
        remaining_tasks = [t for t in remaining_tasks if t.id not in used_ids]

    return DayPlanResult(base_mode=base_mode, blocks=blocks)


def build_day_plan_with_history(
    base_mode: str,
    block_specs: List[DayBlockSpec],
    *,
    filter_spec: Optional[FilterSpec] = None,
) -> DayPlanResult:
    """带历史偏好的日计划版本。

    当没有任何历史记录时，行为会退化为基础版。
    """
    base_mode = (base_mode or "balance").strip().lower()
    if base_mode not in {"rest", "balance", "focus"}:
        base_mode = "balance"

    raw_tasks = load_tasks_from_jsonl()
    if not raw_tasks:
        return DayPlanResult(base_mode=base_mode, blocks=[])

    open_tasks = list(iter_open_tasks(raw_tasks))

    if filter_spec is None:
        filter_spec = FilterSpec()

    remaining_tasks = filter_tasks(open_tasks, filter_spec)

    if not remaining_tasks:
        return DayPlanResult(base_mode=base_mode, blocks=[])

    # 加载历史偏好统计
    history_stats = aggregate_task_stats()

    blocks: List[DayBlockPlan] = []

    for spec in block_specs:
        if not remaining_tasks:
            blocks.append(DayBlockPlan(spec=spec, plan=PlanResult(mode=spec.mode, total_estimated_minutes=0, tasks=[])))
            continue

        plan = _make_block_plan_with_history(remaining_tasks, spec, history_stats=history_stats or None)
        blocks.append(DayBlockPlan(spec=spec, plan=plan))

        used_ids = {pt.task.id for pt in plan.tasks}
        remaining_tasks = [t for t in remaining_tasks if t.id not in used_ids]

    return DayPlanResult(base_mode=base_mode, blocks=blocks)


def day_plan_to_markdown(day_plan: DayPlanResult) -> str:
    """把 DayPlanResult 渲染为 Markdown。"""
    lines: List[str] = []

    lines.append(f"## Day Plan (base_mode = {day_plan.base_mode})")
    lines.append("")
    lines.append(f"- total blocks: **{len(day_plan.blocks)}**")
    lines.append(f"- total estimated minutes: **{day_plan.total_estimated_minutes}**")
    lines.append("")

    if not day_plan.blocks:
        lines.append("> 当前没有可用任务生成日计划。")
        return "\n".join(lines)

    for block in day_plan.blocks:
        spec = block.spec
        plan = block.plan

        lines.append(f"### Block: {spec.name} ({spec.mode})")
        lines.append("")
        lines.append(f"- duration_minutes: `{spec.duration_minutes}`")
        lines.append(f"- max_tasks: `{spec.max_tasks}`")
        lines.append(f"- selected_tasks: `{len(plan.tasks)}`")
        lines.append(f"- total_estimated_minutes: `{plan.total_estimated_minutes}`")
        lines.append("")

        if not plan.tasks:
            lines.append("> 无任务被选入该 block。")
            lines.append("")
            continue

        for idx, planned in enumerate(plan.tasks, start=1):
            t = planned.task
            est = t.estimated_minutes or spec.default_task_minutes
            tags = ", ".join(t.tags) if t.tags else "-"
            reasons = ", ".join(
                f"{k}: {v:+.2f}" for k, v in planned.reasons.items() if abs(v) > 0.01
            )
            lines.append(f"#### {idx}. {t.title}")
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
