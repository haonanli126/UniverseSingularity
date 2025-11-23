from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .execution_review import ExecutionSummary


@dataclass
class NamedExecutionSummary:
    """给 ExecutionSummary 加上 plan 名字，便于展示。"""

    plan_name: str
    summary: ExecutionSummary


@dataclass
class DailyReviewAggregate:
    """汇总一天内多个 plan 的执行情况。"""

    total_plans: int
    total_planned: int
    total_found: int
    total_completed: int
    total_not_completed: int
    total_missing: int
    overall_completion_rate: float
    plans: List[NamedExecutionSummary]


def aggregate_execution_summaries(plans: List[NamedExecutionSummary]) -> DailyReviewAggregate:
    """聚合多份执行 summary，计算总体数据。"""
    total_plans = len(plans)
    total_planned = 0
    total_found = 0
    total_completed = 0
    total_not_completed = 0
    total_missing = 0

    for named in plans:
        s = named.summary
        total_planned += s.total_planned
        total_found += s.found_tasks
        total_completed += s.completed
        total_not_completed += s.not_completed
        total_missing += s.missing

    if total_found > 0:
        overall_completion_rate = total_completed / total_found
    else:
        overall_completion_rate = 0.0

    return DailyReviewAggregate(
        total_plans=total_plans,
        total_planned=total_planned,
        total_found=total_found,
        total_completed=total_completed,
        total_not_completed=total_not_completed,
        total_missing=total_missing,
        overall_completion_rate=overall_completion_rate,
        plans=plans,
    )


def daily_review_to_markdown(agg: DailyReviewAggregate) -> str:
    """把 DailyReviewAggregate 渲染为 Markdown。"""
    lines: List[str] = []

    lines.append("# Daily Plan Execution Review")
    lines.append("")
    lines.append(f"- total plans: **{agg.total_plans}**")
    lines.append(f"- total planned tasks: **{agg.total_planned}**")
    lines.append(f"- tasks found in store: **{agg.total_found}**")
    lines.append(f"- completed: **{agg.total_completed}**")
    lines.append(f"- not completed: **{agg.total_not_completed}**")
    lines.append(f"- missing (not in tasks.jsonl): **{agg.total_missing}**")
    lines.append(f"- overall completion rate (found tasks): **{agg.overall_completion_rate:.2%}**")
    lines.append("")

    if not agg.plans:
        lines.append("> 今天没有任何 plan 需要复盘。")
        return "\n".join(lines)

    for named in agg.plans:
        s = named.summary
        lines.append(f"## Plan: {named.plan_name}")
        lines.append("")
        lines.append(f"- planned tasks: **{s.total_planned}**")
        lines.append(f"- tasks found in store: **{s.found_tasks}**")
        lines.append(f"- completed: **{s.completed}**")
        lines.append(f"- not completed: **{s.not_completed}**")
        lines.append(f"- missing: **{s.missing}**")
        lines.append(f"- completion rate: **{s.completion_rate:.2%}**")
        lines.append("")

    return "\n".join(lines)
