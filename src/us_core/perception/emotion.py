from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


# 非常简洁的中文情绪/能量词典，后面可以慢慢扩展
_POSITIVE_WORDS: Dict[str, float] = {
    "开心": 2.0,
    "高兴": 2.0,
    "兴奋": 2.3,
    "激动": 2.2,
    "期待": 1.5,
    "满意": 1.5,
    "放松": 1.2,
    "平静": 1.0,
    "感激": 1.8,
    "幸福": 2.4,
    "不错": 1.2,
    "还行": 0.8,
}

_NEGATIVE_WORDS: Dict[str, float] = {
    "难过": -2.0,
    "伤心": -2.0,
    "沮丧": -1.8,
    "失望": -1.7,
    "压力": -1.5,
    "焦虑": -1.8,
    "紧张": -1.5,
    "累": -1.3,
    "疲惫": -1.8,
    "困": -1.4,
    "生气": -2.0,
    "愤怒": -2.2,
    "烦": -1.3,
    "崩溃": -2.5,
    "绝望": -3.0,
    "糟糕": -2.0,
    "一般": -0.3,
}

# 能量感知，正数=能量高，负数=能量低
_ENERGY_WORDS: Dict[str, float] = {
    "兴奋": 2.0,
    "激动": 1.8,
    "紧张": 1.2,
    "忙": 1.0,
    "累": -1.5,
    "疲惫": -1.8,
    "困": -1.7,
    "无力": -2.0,
    "想躺": -1.6,
    "想睡": -1.8,
}


@dataclass
class EmotionEstimate:
    """对一段文本的简单情绪估计。"""

    sentiment: str           # "positive" / "negative" / "neutral"
    mood_score: float        # [-1.0, 1.0]，越接近 1 越积极
    energy_level: float      # [-1.0, 1.0]，越接近 1 能量越高
    keywords: List[str]      # 用到的情绪关键词

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentiment": self.sentiment,
            "mood_score": self.mood_score,
            "energy_level": self.energy_level,
            "keywords": list(self.keywords),
        }


def _scan(text: str, lexicon: Dict[str, float]) -> Tuple[float, List[str]]:
    score = 0.0
    matched: List[str] = []
    for word, value in lexicon.items():
        if word and word in text:
            matched.append(word)
            score += value
    return score, matched


def _normalize(raw: float, *, max_abs: float = 3.0) -> float:
    if raw > max_abs:
        raw = max_abs
    if raw < -max_abs:
        raw = -max_abs
    return round(raw / max_abs, 3)  # 压缩到 [-1, 1]，保留三位小数


def estimate_emotion(text: str | None) -> EmotionEstimate:
    """
    规则版情绪估计，不调用任何外部服务。

    设计原则：
    - 文本为空时返回 neutral / 0 分
    - 多个情绪词共存时按简单加权求和
    - 结果是“软判断”，更偏陪伴感，而不是绝对准确
    """
    if not text:
        return EmotionEstimate(
            sentiment="neutral",
            mood_score=0.0,
            energy_level=0.0,
            keywords=[],
        )

    text = text.strip()

    pos_score, pos_words = _scan(text, _POSITIVE_WORDS)
    neg_score, neg_words = _scan(text, _NEGATIVE_WORDS)
    energy_score, energy_words = _scan(text, _ENERGY_WORDS)

    total_mood = pos_score + neg_score  # neg_score 是负数
    mood_norm = _normalize(total_mood)

    if mood_norm > 0.1:
        sentiment = "positive"
    elif mood_norm < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    energy_norm = _normalize(energy_score)

    keywords_set = set(pos_words + neg_words + energy_words)

    return EmotionEstimate(
        sentiment=sentiment,
        mood_score=mood_norm,
        energy_level=energy_norm,
        keywords=sorted(keywords_set),
    )
