from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .channels import InputChannel
from .events import PerceptionEvent, PerceptionStore
from .emotion import EmotionEstimate, estimate_emotion


@dataclass
class TimelineItem:
    """
    用于展示的时间线条目：事件 + 情绪估计。

    这里不修改原始事件，只是在展示层挂上 EmotionEstimate。
    """

    event: PerceptionEvent
    emotion: EmotionEstimate


@dataclass
class TimelineSummary:
    """
    时间线整体的聚合信息，方便做“今日情绪概览”等视图。
    """

    total_events: int
    channels_count: Dict[str, int]
    avg_mood_score: float
    avg_energy_level: float


def _iter_events_for_timeline(
    store: PerceptionStore,
    *,
    channel: Optional[InputChannel] = None,
    limit: int = 20,
) -> Iterable[PerceptionEvent]:
    """
    从 PerceptionStore 中拉取用于时间线展示的事件。

    - 默认从最新往旧排列（reverse=True）
    - 可按 channel 过滤
    """
    return store.iter_events(channel=channel, limit=limit, reverse=True)


def build_timeline(
    store: PerceptionStore,
    *,
    channel: Optional[InputChannel] = None,
    limit: int = 20,
) -> Tuple[List[TimelineItem], TimelineSummary]:
    """
    构建时间线条目 + 聚合信息。

    设计原则：
    - 不依赖事件里是否已经存了 emotion 元数据，统一用 estimate_emotion 重新估计；
      这样旧数据（早期没有 emotion 字段的）也能展示情绪。
    - 聚合信息只针对本次拉取的条目计算。
    """
    events = list(_iter_events_for_timeline(store, channel=channel, limit=limit))

    items: List[TimelineItem] = []
    channel_counter: Counter[str] = Counter()
    mood_sum = 0.0
    energy_sum = 0.0

    for event in events:
        emo = estimate_emotion(event.content)
        items.append(TimelineItem(event=event, emotion=emo))

        channel_counter[event.channel.value] += 1
        mood_sum += emo.mood_score
        energy_sum += emo.energy_level

    total = len(items)
    if total > 0:
        avg_mood = round(mood_sum / total, 3)
        avg_energy = round(energy_sum / total, 3)
    else:
        avg_mood = 0.0
        avg_energy = 0.0

    summary = TimelineSummary(
        total_events=total,
        channels_count=dict(channel_counter),
        avg_mood_score=avg_mood,
        avg_energy_level=avg_energy,
    )
    return items, summary
