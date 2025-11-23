from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .insights import PlannerInsights
from .mode_orchestration import ModeDecision, decide_day_mode
from ..planner.dayplan import (
    DayBlockSpec,
    DayPlanResult,
    build_day_plan_with_history,
    day_plan_to_markdown,
)
from ..planner.models import FilterSpec


@dataclass
class DayModePlanningResult:
    """一天的模式决策 + 对应的日计划结果。"""

    decision: ModeDecision
    day_plan: DayPlanResult


def _build_block_specs_for_mode(
    base_mode: str,
    morning_duration: int,
    afternoon_duration: int,
    evening_duration: int,
    max_tasks_per_block: int,
) -> List[DayBlockSpec]:
    """根据 base_mode 决定早/午/晚的具体 mode 分配。"""

    base_mode = (base_mode or "balance").strip().lower()

    if base_mode == "rest":
        modes = ["rest", "balance", "rest"]
    elif base_mode == "focus":
        modes = ["focus", "focus", "rest"]
    else:  # balance
        modes = ["focus", "balance", "rest"]

    return [
        DayBlockSpec(
            name="morning",
            mode=modes[0],
            duration_minutes=morning_duration,
            max_tasks=max_tasks_per_block,
        ),
        DayBlockSpec(
            name="afternoon",
            mode=modes[1],
            duration_minutes=afternoon_duration,
            max_tasks=max_tasks_per_block,
        ),
        DayBlockSpec(
            name="evening",
            mode=modes[2],
            duration_minutes=evening_duration,
            max_tasks=max_tasks_per_block,
        ),
    ]


def plan_day_with_mood_and_self_model(
    mood_mode: str,
    insights: PlannerInsights,
    *,
    morning_duration: int = 90,
    afternoon_duration: int = 90,
    evening_duration: int = 60,
    max_tasks_per_block: int = 5,
    filter_spec: Optional[FilterSpec] = None,
) -> DayModePlanningResult:
    """用「情绪模式 + 自我模型画像」生成一天的日计划。

    步骤：
    1. 用 decide_day_mode 得到最终 base_mode；
    2. 根据 base_mode 构造 3 个 block 的配置；
    3. 用 build_day_plan_with_history 生成 DayPlanResult。
    """
    decision = decide_day_mode(mood_mode=mood_mode, insights=insights)

    block_specs = _build_block_specs_for_mode(
        base_mode=decision.final_mode,
        morning_duration=morning_duration,
        afternoon_duration=afternoon_duration,
        evening_duration=evening_duration,
        max_tasks_per_block=max_tasks_per_block,
    )

    day_plan = build_day_plan_with_history(
        base_mode=decision.final_mode,
        block_specs=block_specs,
        filter_spec=filter_spec,
    )

    return DayModePlanningResult(decision=decision, day_plan=day_plan)


def day_mode_planning_to_markdown(result: DayModePlanningResult) -> str:
    """把「模式决策 + 日计划」渲染为一份 Markdown。"""
    d = result.decision

    lines: List[str] = []

    lines.append("# Day Plan from Mood × Self-Model")
    lines.append("")
    lines.append(f"- mood-based mode: **{d.mood_mode}**")
    lines.append(f"- self-model mode: **{d.self_model_mode or 'N/A'}**")
    lines.append(f"- final base_mode used for planning: **{d.final_mode}**")
    lines.append("")
    lines.append("## Mode reasoning")
    lines.append("")
    lines.append(d.reason)
    lines.append("")
    lines.append("## Generated day plan")
    lines.append("")
    lines.append(day_plan_to_markdown(result.day_plan))

    return "\n".join(lines)
