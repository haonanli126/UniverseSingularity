from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from .channels import InputChannel
from .events import PerceptionEvent, PerceptionStore
from .emotion import EmotionEstimate, estimate_emotion


@dataclass
class DailySample:
    """用于展示的代表性片段（一条事件 + 对应情绪估计）。"""

    event: PerceptionEvent
    emotion: EmotionEstimate


@dataclass
class DailyMoodSummary:
    """
    某一天的整体情绪画像。

    - total_events: 该日内符合条件的事件数量
    - channels_count: 按渠道统计事件数量（例如 cli_checkin / dialog）
    - sentiment_counts: 按情绪类型统计数量（positive/neutral/negative）
    - avg_mood_score: 平均情绪评分 [-1,1]，越接近 1 越积极
    - avg_energy_level: 平均能量 [-1,1]，越接近 1 能量越高
    - samples: 选出的若干代表性片段
    """

    date: date
    total_events: int
    channels_count: Dict[str, int]
    sentiment_counts: Dict[str, int]
    avg_mood_score: float
    avg_energy_level: float
    samples: List[DailySample]


def _local_date(ts: datetime) -> date:
    """
    将时间戳转换到“用于按日分组”的日期。

    规则：
    - 如果是 naive datetime（无 tzinfo），直接用 ts.date()
    - 如果有 tzinfo，则转为本地时区再取 date()
    """
    if ts.tzinfo is None:
        return ts.date()
    try:
        return ts.astimezone().date()
    except Exception:
        return ts.date()


def build_daily_mood_summary(
    store: PerceptionStore,
    *,
    target_date: Optional[date] = None,
    channel: Optional[InputChannel] = None,
) -> DailyMoodSummary:
    """
    构建某一天的情绪汇总。

    参数：
    - target_date: 要汇总的日期，为空时取“当前本地日期”
    - channel: 限定只统计某个渠道（例如 InputChannel.CLI_CHECKIN），为空则统计所有渠道
    """
    if target_date is None:
        # 使用本地日期作为“今天”的定义
        now_local = datetime.now(timezone.utc).astimezone()
        target_date = now_local.date()

    channels_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    samples_internal: List[tuple[float, int, DailySample]] = []

    mood_sum = 0.0
    energy_sum = 0.0
    total = 0
    index = 0

    for event in store.iter_events(limit=None, reverse=False):
        ev_date = _local_date(event.timestamp)
        if ev_date != target_date:
            continue

        if channel is not None and event.channel is not channel:
            continue

        emotion = estimate_emotion(event.content)

        total += 1
        mood_sum += emotion.mood_score
        energy_sum += emotion.energy_level

        channels_counter[event.channel.value] += 1
        sentiment_counter[emotion.sentiment] += 1

        # 代表性片段：按情绪强度（|mood_score|）排序，保留 top N
        strength = abs(emotion.mood_score)
        samples_internal.append((strength, index, DailySample(event=event, emotion=emotion)))
        index += 1

    if total > 0:
        avg_mood = round(mood_sum / total, 3)
        avg_energy = round(energy_sum / total, 3)
    else:
        avg_mood = 0.0
        avg_energy = 0.0

    # 选出最多 3 条代表性片段
    samples_internal.sort(key=lambda x: (-x[0], x[1]))
    top_samples = [item[2] for item in samples_internal[:3]]

    summary = DailyMoodSummary(
        date=target_date,
        total_events=total,
        channels_count=dict(channels_counter),
        sentiment_counts=dict(sentiment_counter),
        avg_mood_score=avg_mood,
        avg_energy_level=avg_energy,
        samples=top_samples,
    )
    return summary
