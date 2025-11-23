from __future__ import annotations

from typing import List

from .insights import PlannerInsights, TagStats
from .mode_orchestration import ModeDecision


def _select_significant_tags(
    tag_stats: List[TagStats],
    *,
    min_planned_per_tag: int,
) -> List[TagStats]:
    return [ts for ts in tag_stats if ts.times_planned >= min_planned_per_tag]


def _split_best_worst(
    tags: List[TagStats],
    *,
    top_n: int,
) -> tuple[List[TagStats], List[TagStats]]:
    if not tags:
        return [], []

    # 按完成率降序 + 次数降序 → 最强标签
    best = sorted(
        tags,
        key=lambda s: (s.completion_rate, s.times_planned),
        reverse=True,
    )[:top_n]

    # 按完成率升序 + 次数降序 → 阻力标签
    worst = sorted(
        tags,
        key=lambda s: (s.completion_rate, s.times_planned),
    )[:top_n]

    return best, worst


def build_daily_self_story(
    decision: ModeDecision,
    insights: PlannerInsights,
    *,
    top_n: int = 3,
    min_planned_per_tag: int = 3,
) -> str:
    """基于模式决策 + Planner 执行画像，生成一段「自我叙事」Markdown。

    这里不尝试做真正的自然语言生成，而是用结构化信息拼出一份
    人类可读、稳定可测试的文本。
    """
    lines: List[str] = []

    lines.append("# Daily Self Story: Planner Perspective")
    lines.append("")
    lines.append(f"- final_mode: **{decision.final_mode}**")
    lines.append(f"- mood_mode: **{decision.mood_mode}**")
    lines.append(f"- self_model_mode: **{decision.self_model_mode or 'N/A'}**")
    lines.append(f"- overall_completion_rate: **{insights.overall_completion_rate:.2%}**")
    lines.append("")

    # 没有任何历史记录时，给出简短说明即可
    if insights.total_planned_events == 0:
        lines.append("## Summary")
        lines.append("")
        lines.append(
            "今天我的节奏完全由情绪系统决定，因为自我模型里还没有任何执行历史。"
        )
        lines.append(
            "接下来的几天，只要我持续使用 Planner 规划任务，并在日终执行复盘，"
            "这个自我故事会逐渐从「空白」变成「真正在描述我的习惯」。"
        )
        return "\n".join(lines)

    # 有历史记录时，展开更多细节
    significant_tags = _select_significant_tags(
        insights.tag_stats,
        min_planned_per_tag=min_planned_per_tag,
    )
    best, worst = _split_best_worst(significant_tags, top_n=top_n)

    lines.append("## Summary")
    lines.append("")
    if decision.final_mode == "rest":
        lines.append(
            "今天整体建议的节奏是 **rest** 模式：我更需要恢复和重建节奏，"
            "而不是一味向前冲刺。"
        )
    elif decision.final_mode == "focus":
        lines.append(
            "今天整体建议的节奏是 **focus** 模式：我有能力在关键任务上打一波进攻，"
            "把长期想推进的事情向前挪动一点。"
        )
    else:
        lines.append(
            "今天整体建议的节奏是 **balance** 模式：在推进重要任务的同时，"
            "也刻意为自己保留恢复和整理的空间。"
        )

    lines.append(
        f"从历史数据看，我整体的任务完成率大约是 **{insights.overall_completion_rate:.1%}**。"
    )
    lines.append(
        "这代表了我最近一段时间的「执行节奏感」，"
        "既不是完美主义，也不是完全躺平，而是一种真实的生活步调。"
    )
    lines.append("")

    if best:
        lines.append("## What I tend to finish (强项任务类型)")
        lines.append("")
        for ts in best:
            lines.append(
                f"- `{ts.tag}`：完成率 **{ts.completion_rate:.1%}** "
                f"(规划 {ts.times_planned} 次，完成 {ts.times_completed} 次)"
            )
        lines.append("")
        lines.append(
            "这些标签代表了我比较顺手、容易进入状态的任务类型。"
            "当我想重建信心或快速“找回手感”时，可以优先从这里挑一两个任务开始。"
        )
        lines.append("")

    if worst:
        lines.append("## What I keep postponing (阻力任务类型)")
        lines.append("")
        for ts in worst:
            lines.append(
                f"- `{ts.tag}`：完成率 **{ts.completion_rate:.1%}** "
                f"(规划 {ts.times_planned} 次，完成 {ts.times_completed} 次)"
            )
        lines.append("")
        lines.append(
            "这些标签往往是我反复写进计划、却总是没做完的任务类型。"
            "它们不一定是坏事，可能只是需要被拆成更小的步骤，"
            "或者换一个更轻松的节奏去靠近。"
        )
        lines.append("")

    lines.append("## How I want to treat myself today")
    lines.append("")
    if decision.final_mode == "rest":
        lines.append(
            "- 给自己多一点宽容：允许任务列表不那么完美，"
            "把注意力放在恢复能量、清理堆积的情绪和杂事上。"
        )
    elif decision.final_mode == "focus":
        lines.append(
            "- 给关键任务更多优先级：挑 1~2 个真正重要、带有 `universe` 或 deep-work 标签的任务，"
            "安排在状态最好的时间段完成。"
        )
    else:
        lines.append(
            "- 在推进和照顾之间找到平衡："
            "既安排 `universe` 等长期目标任务，也预留 `self-care` 的时间，"
            "让节奏既有推进感，又不会过度透支。"
        )

    return "\n".join(lines)
