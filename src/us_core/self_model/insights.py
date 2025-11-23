from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from ..planner.preference_memory import aggregate_task_stats, attach_task_metadata


@dataclass
class TagStats:
    tag: str
    times_planned: int
    times_completed: int

    @property
    def completion_rate(self) -> float:
        if self.times_planned == 0:
            return 0.0
        return self.times_completed / self.times_planned


@dataclass
class PlannerInsights:
    """对 Planner 行为的整体画像。"""

    total_tasks: int
    total_planned_events: int
    total_completed_events: int
    overall_completion_rate: float
    tag_stats: List[TagStats]


def compute_insights_from_enriched(enriched: List[dict]) -> PlannerInsights:
    """输入 attach_task_metadata 产出的 enriched 列表，计算整体画像。"""
    total_tasks = len(enriched)
    total_planned_events = 0
    total_completed_events = 0

    tag_stats_map: Dict[str, TagStats] = {}

    for entry in enriched:
        times_planned = int(entry.get("times_planned", 0) or 0)
        times_completed = int(entry.get("times_completed", 0) or 0)
        tags = entry.get("tags") or []

        total_planned_events += times_planned
        total_completed_events += times_completed

        for tag in tags:
            t = str(tag).lower()
            stats = tag_stats_map.get(t)
            if stats is None:
                stats = TagStats(tag=t, times_planned=0, times_completed=0)
                tag_stats_map[t] = stats
            stats.times_planned += times_planned
            stats.times_completed += times_completed

    if total_planned_events > 0:
        overall_completion_rate = total_completed_events / total_planned_events
    else:
        overall_completion_rate = 0.0

    tag_stats = list(tag_stats_map.values())
    # 先按完成率降序，再按次数降序，保证稳定
    tag_stats.sort(key=lambda s: (s.completion_rate, s.times_planned), reverse=True)

    return PlannerInsights(
        total_tasks=total_tasks,
        total_planned_events=total_planned_events,
        total_completed_events=total_completed_events,
        overall_completion_rate=overall_completion_rate,
        tag_stats=tag_stats,
    )


def load_planner_insights(
    *,
    history_path=None,
    tasks_path=None,
) -> PlannerInsights:
    """从 planner_history.jsonl + tasks.jsonl 加载并计算画像。

    - 没有历史记录时，返回全 0 / 空列表。
    """
    stats = aggregate_task_stats(history_path)
    if not stats:
        return PlannerInsights(
            total_tasks=0,
            total_planned_events=0,
            total_completed_events=0,
            overall_completion_rate=0.0,
            tag_stats=[],
        )

    enriched = attach_task_metadata(stats, tasks_path=tasks_path)
    return compute_insights_from_enriched(enriched)


def insights_to_markdown(
    insights: PlannerInsights,
    *,
    top_n: int = 3,
    min_planned_per_tag: int = 3,
) -> str:
    """把 PlannerInsights 渲染为一份「自我画像」Markdown。"""
    lines: List[str] = []

    lines.append("# Self Model Snapshot: Planner Habits")
    lines.append("")
    lines.append(f"- distinct tasks seen in history: **{insights.total_tasks}**")
    lines.append(f"- total planned events: **{insights.total_planned_events}**")
    lines.append(f"- total completed events: **{insights.total_completed_events}**")
    lines.append(f"- overall completion rate: **{insights.overall_completion_rate:.2%}**")
    lines.append("")

    if insights.total_planned_events == 0:
        lines.append("> 当前还没有任何 Planner 执行历史，请先运行执行复盘脚本。")
        return "\n".join(lines)

    # 过滤出至少被规划过 min_planned_per_tag 次的标签
    significant_tags = [
        ts for ts in insights.tag_stats if ts.times_planned >= min_planned_per_tag
    ]

    if not significant_tags:
        lines.append(f"> 目前还没有任何标签被规划超过 {min_planned_per_tag} 次，样本量太少，暂时无法给出可靠偏好。")
        return "\n".join(lines)

    # 按完成率升序/降序切片
    sorted_tags = list(sorted(significant_tags, key=lambda s: s.completion_rate, reverse=True))

    best = sorted_tags[:top_n]
    worst = list(sorted(significant_tags, key=lambda s: s.completion_rate))[:top_n]

    lines.append("## Tags with highest completion rate")
    lines.append("")
    for ts in best:
        lines.append(
            f"- `{ts.tag}`: completion **{ts.completion_rate:.1%}** "
            f"(planned={ts.times_planned}, completed={ts.times_completed})"
        )
    lines.append("")

    lines.append("## Tags with lowest completion rate")
    lines.append("")
    for ts in worst:
        lines.append(
            f"- `{ts.tag}`: completion **{ts.completion_rate:.1%}** "
            f"(planned={ts.times_planned}, completed={ts.times_completed})"
        )
    lines.append("")

    lines.append("## Interpretation (for the human self)")
    lines.append("")
    lines.append(
        "- 高完成率标签：说明你在这类任务上更容易进入状态，是你的「惯性优势区」。"
    )
    lines.append(
        "- 低完成率标签：往往是被你反复规划、却总被拖延的任务类型，之后 Planner 可以对它们采用更温和的节奏（拆小块 / 放在能量更高的时段）。"
    )

    return "\n".join(lines)
