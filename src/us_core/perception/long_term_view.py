from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..core.workspace import LongTermMemoryItem
from ..core.mood import (
    build_mood_samples_from_long_term,
    aggregate_daily_mood,
    DailyMood,
)


def load_memory_items_from_jsonl(path: Path) -> List[LongTermMemoryItem]:
    """
    从 JSONL 文件中加载 LongTermMemoryItem 列表。

    预期每行形如：
      {"text": "...", "intent_label": "emotion", "timestamp": "2025-01-01T10:00:00+00:00"}

    - 文件不存在时返回空列表
    - 解析失败 / 字段不完整的行会被跳过
    """
    items: List[LongTermMemoryItem] = []

    if not path.exists():
        return items

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = str(data.get("text") or "").strip()
            intent = str(data.get("intent_label") or "").strip() or "emotion"
            ts_raw = data.get("timestamp")

            if not text or not ts_raw:
                continue

            try:
                ts = datetime.fromisoformat(ts_raw)
            except Exception:
                continue

            items.append(
                LongTermMemoryItem(
                    text=text,
                    intent_label=intent,
                    timestamp=ts,
                )
            )

    return items


def build_daily_mood_from_memory_file(path: Path) -> List[DailyMood]:
    """
    从 JSONL 文件中加载长期记忆条目，并按天聚合情绪。

    返回按日期排序的 DailyMood 列表。
    """
    items = load_memory_items_from_jsonl(path)
    if not items:
        return []

    samples = build_mood_samples_from_long_term(items)
    daily = aggregate_daily_mood(samples)
    return daily
