from __future__ import annotations

"""
测试情绪雷达模块（Mood Analyzer v0）
"""

from datetime import datetime, timedelta, timezone

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.workspace import LongTermMemoryItem
from src.us_core.core.mood import (
    classify_text_mood,
    mood_label,
    build_mood_samples_from_long_term,
    build_mood_samples_from_journal_events,
    aggregate_daily_mood,
)


def _now():
    return datetime.now(timezone.utc)


def test_classify_text_mood_positive_negative_neutral():
    pos_text = "今天很开心，也比较放松。"
    neg_text = "今天好累，有点焦虑和压力。"
    neu_text = "今天就是普通的一天。"

    assert classify_text_mood(pos_text) > 0
    assert classify_text_mood(neg_text) < 0
    assert classify_text_mood(neu_text) == 0


def test_build_mood_samples_from_long_term_only_emotion():
    now = _now()
    items = [
        LongTermMemoryItem(
            text="我最近有点累，也有点焦虑。",
            intent_label="emotion",
            timestamp=now - timedelta(days=1),
        ),
        LongTermMemoryItem(
            text="帮我想想 Phase 1 下一步应该做什么。",
            intent_label="command",
            timestamp=now,
        ),
    ]

    samples = build_mood_samples_from_long_term(items)
    # 只应该提取 emotion 这一条
    assert len(samples) == 1
    s = samples[0]
    assert s.source == "long_term"
    assert s.score < 0
    assert "累" in s.text or "焦虑" in s.text


def test_build_mood_samples_from_journal_events_only_journal():
    now = _now()
    ev1 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(hours=2),
        payload={"kind": "journal_entry", "text": "今天整体还算平静，只是有点累。"},
    )
    ev2 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(hours=1),
        payload={"kind": "note", "text": "这不是日记。"},
    )

    samples = build_mood_samples_from_journal_events([ev1, ev2])
    assert len(samples) == 1
    s = samples[0]
    assert s.source == "journal"
    assert s.score != 0  # 有“平静”和“累”，分数可能接近中性，但不为 0


def test_aggregate_daily_mood_basic():
    now = _now()
    items = [
        LongTermMemoryItem(
            text="我最近有点累，也有点焦虑。",
            intent_label="emotion",
            timestamp=now - timedelta(days=1, hours=1),
        ),
        LongTermMemoryItem(
            text="今天心态比昨天好一点，有一点点期待。",
            intent_label="emotion",
            timestamp=now - timedelta(days=1, hours=2),
        ),
    ]

    samples = build_mood_samples_from_long_term(items)
    daily = aggregate_daily_mood(samples)

    assert len(daily) == 1
    d = daily[0]
    assert d.sample_count == 2
    # 平均值应该在 [-2, 2] 区间内
    assert -2.0 <= d.average_score <= 2.0
    assert isinstance(d.label, str) and d.label
