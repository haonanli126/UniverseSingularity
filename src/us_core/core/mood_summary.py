from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .mood import DailyMood, mood_label


@dataclass
class WeeklyMoodSummary:
    """
    一段时间（通常是 7 天左右）的情绪总结。

    - days: 按日期排序的 DailyMood 列表
    - overall_average: 整体平均情绪（简单取 daily.average_score 的平均）
    - overall_label: 人类可读的情绪标签（通过 mood_label 计算）
    - best_day: 情绪最高的一天（可能为 None）
    - worst_day: 情绪最低的一天（可能为 None）
    """

    days: List[DailyMood]
    overall_average: float
    overall_label: str
    best_day: Optional[DailyMood]
    worst_day: Optional[DailyMood]


def summarize_weekly_mood(daily: List[DailyMood]) -> WeeklyMoodSummary:
    """
    根据若干天的 DailyMood，生成一个整体的 WeeklyMoodSummary。

    这里不强制天数必须是 7，只要传入若干天即可。
    """
    if not daily:
        return WeeklyMoodSummary(
            days=[],
            overall_average=0.0,
            overall_label=mood_label(0.0),
            best_day=None,
            worst_day=None,
        )

    # 确保按日期排序
    days_sorted = sorted(daily, key=lambda d: d.day)

    # 简单取平均值（未来如果想按照 sample_count 加权也可以升级）
    avg = sum(d.average_score for d in days_sorted) / len(days_sorted)
    avg = round(avg, 3)
    label = mood_label(avg)

    best = max(days_sorted, key=lambda d: d.average_score)
    worst = min(days_sorted, key=lambda d: d.average_score)

    return WeeklyMoodSummary(
        days=days_sorted,
        overall_average=avg,
        overall_label=label,
        best_day=best,
        worst_day=worst,
    )


def generate_weekly_mood_summary_text(summary: WeeklyMoodSummary) -> str:
    """
    根据 WeeklyMoodSummary 生成一段适合作为「一周情绪小结」的中文描述。
    """

    if not summary.days:
        return "这段时间还没有记录到你的情绪足迹，有空可以和我多聊聊。"

    first_day = summary.days[0].day.isoformat()
    last_day = summary.days[-1].day.isoformat()
    day_count = len(summary.days)

    lines: List[str] = []

    # 段落 1：整体概况
    lines.append(
        f"从 {first_day} 到 {last_day}（共 {day_count} 天），"
        f"整体情绪可以形容为：{summary.overall_label}。"
    )
    lines.append(
        f"这一段时间的平均情绪分为 {summary.overall_average:+.2f} "
        f"（越接近 1 越偏正面，越接近 -1 越偏负面）。"
    )

    # 统计正负天数
    positive_days = [d for d in summary.days if d.average_score > 0.2]
    negative_days = [d for d in summary.days if d.average_score < -0.2]

    if positive_days and negative_days:
        lines.append(
            "这几天的状态有一定波动，既有比较轻松、偏正面的日子，"
            "也有情绪更低落、压力偏大的时候。"
        )
    elif positive_days:
        lines.append(
            "整体上，更多的日子是偏正面、偏轻松的，你在一点点往前走。"
        )
    elif negative_days:
        lines.append(
            "整体上，更多的日子是偏负面的，说明这段时间你承受了不少压力。"
        )
    else:
        lines.append(
            "整体上，这几天的情绪比较平稳，没有特别明显的高峰或低谷。"
        )

    # 段落 2：最好的一天 / 最难的一天
    if summary.best_day is not None:
        bd = summary.best_day
        lines.append(
            f"在这段时间里，情绪相对最好的一天大约是 {bd.day.isoformat()}，"
            f"那天整体感觉是「{bd.label}」，"
            f"平均情绪分为 {bd.average_score:+.2f}。"
        )

    if summary.worst_day is not None:
        wd = summary.worst_day
        lines.append(
            f"相对来说，情绪最吃力的一天大约是 {wd.day.isoformat()}，"
            f"那天的整体状态是「{wd.label}」，"
            f"平均情绪分为 {wd.average_score:+.2f}。"
        )

    # 段落 3：温柔一点的收尾（不做诊断，只做陪伴）
    lines.append(
        "无论这几天是偏轻松还是偏辛苦，都谢谢你愿意把这些片段留下来。"
        "如果以后哪天累了、慌了，随时可以再来和我讲讲，我们一起把这些情绪消化掉。"
    )

    return "\n".join(lines)
