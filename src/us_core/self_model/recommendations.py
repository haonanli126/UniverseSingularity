from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .insights import PlannerInsights, TagStats


@dataclass
class SelfModelRecommendations:
    """基于 PlannerInsights 给出的高层策略建议。"""

    insights: PlannerInsights
    strength_tags: List[TagStats]
    friction_tags: List[TagStats]
    suggested_base_mode: str  # "rest" / "balance" / "focus"


def _find_tag(insights: PlannerInsights, name: str) -> Optional[TagStats]:
    name = name.lower()
    for ts in insights.tag_stats:
        if ts.tag == name:
            return ts
    return None


def suggest_base_mode_from_insights(insights: PlannerInsights) -> str:
    """根据整体完成率 + 某些关键标签的表现，给出推荐 base_mode。"""
    # 无历史：保持中性
    if insights.total_planned_events == 0:
        return "balance"

    overall = insights.overall_completion_rate

    self_care = _find_tag(insights, "self-care")
    universe = _find_tag(insights, "universe")

    # 整体完成率很低：建议偏 rest，减压 + 多安排自我照顾
    if overall < 0.4:
        return "rest"

    # 整体完成率很高：说明你普遍执行力不错，可以偏 focus
    if overall > 0.75:
        return "focus"

    # 中间区间，用标签做细化判断
    # 如果 self-care 被规划很多但完成率偏低，说明自我照顾老被你拖延 → 倾向 rest
    if self_care and self_care.times_planned >= 3 and self_care.completion_rate < 0.5:
        return "rest"

    # 如果 self-care 完成率很高，而 universe 完成率偏低，说明你在“舒适区”表现好，但大目标推进不足 → 倾向 focus
    if (
        self_care
        and universe
        and self_care.times_planned >= 3
        and universe.times_planned >= 3
        and self_care.completion_rate > 0.7
        and universe.completion_rate < 0.5
    ):
        return "focus"

    # 默认保持 balance
    return "balance"


def build_self_model_recommendations(
    insights: PlannerInsights,
    *,
    min_planned_per_tag: int = 3,
    top_n: int = 3,
) -> SelfModelRecommendations:
    """从 PlannerInsights 生成一份结构化的策略建议。"""
    if insights.total_planned_events == 0:
        # 没有历史：空列表 + balance
        return SelfModelRecommendations(
            insights=insights,
            strength_tags=[],
            friction_tags=[],
            suggested_base_mode="balance",
        )

    significant_tags = [
        ts for ts in insights.tag_stats if ts.times_planned >= min_planned_per_tag
    ]

    # 可能历史太少，没有任何标签达到阈值，也要能处理
    if significant_tags:
        strength_tags = sorted(
            significant_tags,
            key=lambda s: (s.completion_rate, s.times_planned),
            reverse=True,
        )[:top_n]

        friction_tags = sorted(
            significant_tags,
            key=lambda s: (s.completion_rate, -s.times_planned),
        )[:top_n]
    else:
        strength_tags = []
        friction_tags = []

    suggested = suggest_base_mode_from_insights(insights)

    return SelfModelRecommendations(
        insights=insights,
        strength_tags=strength_tags,
        friction_tags=friction_tags,
        suggested_base_mode=suggested,
    )


def recommendations_to_markdown(rec: SelfModelRecommendations) -> str:
    """把 SelfModelRecommendations 渲染为 Markdown 文本。"""
    insights = rec.insights
    lines: List[str] = []

    lines.append("# Self Model Recommendations: Planner Strategy")
    lines.append("")
    lines.append(
        f"- distinct tasks seen in history: **{insights.total_tasks}**"
    )
    lines.append(
        f"- total planned events: **{insights.total_planned_events}**"
    )
    lines.append(
        f"- total completed events: **{insights.total_completed_events}**"
    )
    lines.append(
        f"- overall completion rate: **{insights.overall_completion_rate:.2%}**"
    )
    lines.append(
        f"- suggested base_mode for tomorrow: **{rec.suggested_base_mode}**"
    )
    lines.append("")

    if insights.total_planned_events == 0:
        lines.append("> 当前还没有 Planner 执行历史，建议先运行几天计划 + 执行复盘后再来看。")
        return "\n".join(lines)

    if not rec.strength_tags and not rec.friction_tags:
        lines.append(
            "> 目前没有任何标签被规划超过指定次数，样本量偏少，先保持默认的 balance 模式。"
        )
        return "\n".join(lines)

    if rec.strength_tags:
        lines.append("## Strength tags (你最容易完成的任务类型)")
        lines.append("")
        for ts in rec.strength_tags:
            lines.append(
                f"- `{ts.tag}`: completion **{ts.completion_rate:.1%}** "
                f"(planned={ts.times_planned}, completed={ts.times_completed})"
            )
        lines.append("")

    if rec.friction_tags:
        lines.append("## Friction tags (最容易被拖延的任务类型)")
        lines.append("")
        for ts in rec.friction_tags:
            lines.append(
                f"- `{ts.tag}`: completion **{ts.completion_rate:.1%}** "
                f"(planned={ts.times_planned}, completed={ts.times_completed})"
            )
        lines.append("")

    lines.append("## Suggested strategy for tomorrow")
    lines.append("")
    mode = rec.suggested_base_mode
    if mode == "rest":
        lines.append(
            "- 建议把明天视为「恢复 / 重建节奏」的一天："
        )
        lines.append("  - 至少安排 1 个纯 self-care block；")
        lines.append("  - 给长线任务减负，只选 1~2 个最重要的；")
        lines.append("  - 用更多时间做整理、复盘、睡眠和身体恢复。")
    elif mode == "focus":
        lines.append(
            "- 建议把明天视为「进攻 / 推进关键项目」的一天："
        )
        lines.append("  - 上午安排 1 个高强度 universe / deep-work block；")
        lines.append("  - 自我照顾保持「刚好够」，防止透支；")
        lines.append("  - 把一直想做但总没排上的大任务放进清晨或状态最好的时间段。")
    else:  # balance
        lines.append(
            "- 建议把明天视为「平衡 / 调优节奏」的一天："
        )
        lines.append("  - 早上安排 1 个 focus block 用来推进 universe 类任务；")
        lines.append("  - 下午 / 晚上安排 1~2 个 self-care / maintenance 任务；")
        lines.append("  - 刻意避免把同一类高压任务排满一整天。")

    return "\n".join(lines)
