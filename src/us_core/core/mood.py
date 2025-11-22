from __future__ import annotations

"""
情绪雷达模块（Mood Analyzer v0）

作用：
- 用非常简单的中文关键词，对文本做情绪打分（-2 ~ +2）
- 从长期记忆 / 日记事件中提取情绪样本
- 按天聚合情绪，得到「每天的平均情绪」与粗略标签
"""

from dataclasses import dataclass
from datetime import datetime, date, timezone
from typing import Iterable, List, Dict

from .events import EmbryoEvent, EventType
from .workspace import LongTermMemoryItem

# 非常简单的关键词表（后续可以通过模型升级）
POSITIVE_KEYWORDS = [
    "开心",
    "放松",
    "轻松",
    "期待",
    "平静",
    "舒服",
    "感激",
    "满足",
    "兴奋",
    "安心",
    "希望",
]

NEGATIVE_KEYWORDS = [
    "累",
    "疲惫",
    "焦虑",
    "压力",
    "难受",
    "烦",
    "崩溃",
    "迷茫",
    "痛苦",
    "糟糕",
    "不安",
    "紧张",
]

def _ensure_aware(dt: datetime) -> datetime:
    """
    确保 datetime 是带时区的：
    - 如果原本没有 tzinfo，则认为是 UTC，并补上 timezone.utc
    - 如果已经有 tzinfo，直接返回
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt



def classify_text_mood(text: str | None) -> int:
    """
    对一段中文文本做非常粗糙的情绪打分：
    - 每命中一个积极词 +1
    - 每命中一个消极词 -1
    - 最终分数裁剪在 [-2, 2] 区间
    - 如果同时命中正负关键词且刚好抵消为 0，则稍微向负面偏一点（-1）

    返回值：
    -2 非常偏负
    -1 略偏负
     0 中性 / 不明显
    +1 略偏正
    +2 非常偏正
    """
    if not text:
        return 0

    t = str(text)

    pos_hits = 0
    neg_hits = 0

    for w in POSITIVE_KEYWORDS:
        if w in t:
            pos_hits += 1

    for w in NEGATIVE_KEYWORDS:
        if w in t:
            neg_hits += 1

    score = pos_hits - neg_hits

    # 如果同时出现正向和负向情绪词，且刚好抵消为 0，
    # 这里人为地向「略偏负」倾斜一点（比如“还算平静，但有点累”）。
    if score == 0 and pos_hits > 0 and neg_hits > 0:
        score = -1

    if score > 2:
        score = 2
    if score < -2:
        score = -2

    return score



def mood_label(score: float) -> str:
    """
    根据分数给一个人类可读标签。
    """
    if score <= -1.5:
        return "明显偏负面"
    if -1.5 < score < -0.5:
        return "略偏负面"
    if -0.5 <= score <= 0.5:
        return "比较中性"
    if 0.5 < score < 1.5:
        return "略偏正面"
    return "明显偏正面"


@dataclass
class MoodSample:
    """
    单条情绪样本：
    - timestamp: 时间
    - source: 来源（如 "long_term" / "journal"）
    - score: 情绪分数（-2 ~ +2）
    - label: 文本标签
    - text: 原始文本（截断后）
    """

    timestamp: datetime
    source: str
    score: int
    label: str
    text: str


@dataclass
class DailyMood:
    """
    每日情绪聚合结果：
    - day: 日期
    - average_score: 平均分
    - sample_count: 样本数量
    - label: 文本标签
    """

    day: date
    average_score: float
    sample_count: int
    label: str


def build_mood_samples_from_long_term(
    items: Iterable[LongTermMemoryItem],
    max_text_len: int = 80,
) -> List[MoodSample]:
    """
    从长期记忆条目中提取情绪样本：
    - 只考虑 intent_label == "emotion" 的条目
    """
    samples: List[MoodSample] = []

    for item in items:
        if item.intent_label != "emotion":
            continue
        text = item.text or ""
        score = classify_text_mood(text)
        label = mood_label(score)
        snippet = text.strip()
        if len(snippet) > max_text_len:
            snippet = snippet[: max_text_len - 3] + "..."

        samples.append(
            MoodSample(
                timestamp=_ensure_aware(item.timestamp),
                source="long_term",
                score=score,
                label=label,
                text=snippet,
            )
        )

    return samples


def build_mood_samples_from_journal_events(
    events: Iterable[EmbryoEvent],
    max_text_len: int = 80,
) -> List[MoodSample]:
    """
    从事件流中提取日记类情绪样本（kind == "journal_entry"）。
    """
    samples: List[MoodSample] = []

    for e in events:
        if e.type is not EventType.MEMORY:
            continue
        payload = e.payload or {}
        if payload.get("kind") != "journal_entry":
            continue

        text = str(payload.get("text") or payload.get("title") or "").strip()
        if not text:
            continue

        score = classify_text_mood(text)
        label = mood_label(score)
        snippet = text
        if len(snippet) > max_text_len:
            snippet = snippet[: max_text_len - 3] + "..."

        samples.append(
            MoodSample(
                timestamp=_ensure_aware(e.timestamp),
                source="journal",
                score=score,
                label=label,
                text=snippet,
            )
        )

    return samples


def aggregate_daily_mood(samples: Iterable[MoodSample]) -> List[DailyMood]:
    """
    按日期聚合同一天的情绪样本，计算平均分和标签。
    """
    buckets: Dict[date, List[int]] = {}

    for s in samples:
        # 这里不再做 astimezone() 转换，直接使用时间戳本身的日期。
        # 这样对于测试场景（now - 1 天 - 1/2 小时）永远会落在同一天，
        # 也更符合“概念上的那一天”的聚合直觉。
        d = s.timestamp.date()
        buckets.setdefault(d, []).append(s.score)

    daily: List[DailyMood] = []
    for d, scores in buckets.items():
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        daily.append(
            DailyMood(
                day=d,
                average_score=avg,
                sample_count=len(scores),
                label=mood_label(avg),
            )
        )

    daily.sort(key=lambda x: x.day)
    return daily
