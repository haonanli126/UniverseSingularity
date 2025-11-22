from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from .mood import DailyMood
from .mood_summary import WeeklyMoodSummary, summarize_weekly_mood
from .self_care import SelfCareSuggestion, build_self_care_suggestion


@dataclass
class DailyReflectionContext:
    """
    日终小结的核心数据结构（Phase 3-S02）：

    - today: 认为的“今天”的日期（通常是当前本地日期）
    - today_mood: 如果有的话，今天的 DailyMood；如果今天没有记录，则为 None
    - days_used: 纳入本次小结的 DailyMood 列表（按日期升序）
    - weekly_summary: 对 days_used 这段时间的情绪总结
    - self_care: 基于 days_used 给出的自我照顾建议；如果 days_used 为空则为 None
    """

    today: date
    today_mood: Optional[DailyMood]
    days_used: List[DailyMood]
    weekly_summary: WeeklyMoodSummary
    self_care: Optional[SelfCareSuggestion]


def build_daily_reflection_context(
    daily: List[DailyMood],
    *,
    today: date,
    days_window: int = 7,
) -> DailyReflectionContext:
    """
    根据一串 DailyMood，构造日终小结所需的上下文。

    逻辑：
      1. 将 daily 按日期排序
      2. 从末尾往前取最多 days_window 天，作为 days_used
      3. 在整个 daily 中查找今天对应的 DailyMood（如果有）
      4. 对 days_used 做 weekly_summary（其实是“最近 N 天总结”）
      5. 对 days_used 做 self_care 建议

    注意：这里不读文件，也不关心时区，只做纯数据层处理。
    """
    if not daily:
        # 即使没有 data，也要返回一个结构，让上层决定怎么提示用户
        empty_summary = summarize_weekly_mood([])
        return DailyReflectionContext(
            today=today,
            today_mood=None,
            days_used=[],
            weekly_summary=empty_summary,
            self_care=None,
        )

    # 1）按日期升序排序
    daily_sorted = sorted(daily, key=lambda d: d.day)

    # 2）从末尾往前取最多 days_window 天
    if days_window <= 0:
        days_window = 1
    if len(daily_sorted) > days_window:
        days_used = daily_sorted[-days_window:]
    else:
        days_used = daily_sorted

    # 3）查找今天对应的 DailyMood（在整个 daily 中找）
    today_mood = next((d for d in daily_sorted if d.day == today), None)

    # 4）最近 N 天总结
    weekly_summary = summarize_weekly_mood(days_used)

    # 5）自我照顾建议（基于最近 N 天）
    self_care = build_self_care_suggestion(days_used)

    return DailyReflectionContext(
        today=today,
        today_mood=today_mood,
        days_used=days_used,
        weekly_summary=weekly_summary,
        self_care=self_care,
    )
