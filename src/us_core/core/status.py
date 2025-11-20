from __future__ import annotations

"""
状态统计模块：给数字胚胎一个简单的「自我状态面板」。

- 统计对话日志中的消息数量 / 最近时间
- 统计自省日志中的条数 / 最近时间
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .events import EmbryoEvent
from .persistence import load_events_from_jsonl


@dataclass
class ConversationStats:
    total_events: int
    total_messages: int
    last_timestamp: Optional[datetime]


@dataclass
class ReflectionStats:
    total_events: int
    last_timestamp: Optional[datetime]


def get_conversation_stats(session_log_path: Path) -> ConversationStats:
    """
    统计会话日志中的基础信息。

    - total_events: JSONL 中 EmbryoEvent 总数
    - total_messages: 其中 payload 包含 role/text 的条数
    - last_timestamp: 最后一条事件的 timestamp（UTC）
    """
    events = load_events_from_jsonl(session_log_path)
    total_events = len(events)

    total_messages = 0
    last_ts: Optional[datetime] = None

    for e in events:
        payload = e.payload or {}
        if "role" in payload and "text" in payload:
            total_messages += 1

        ts = e.timestamp
        # 统一成带时区的时间，避免 naive / aware 混用导致 TypeError
        if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
            ts = ts.replace(tzinfo=timezone.utc)

        if last_ts is None or ts > last_ts:
            last_ts = ts

    return ConversationStats(
        total_events=total_events,
        total_messages=total_messages,
        last_timestamp=last_ts,
    )


def get_reflection_stats(reflection_log_path: Path) -> ReflectionStats:
    """
    统计自省日志中的基础信息。

    - total_events: 自省事件数量
    - last_timestamp: 最后一条自省的时间
    """
    events = load_events_from_jsonl(reflection_log_path)
    total_events = len(events)

    last_ts: Optional[datetime] = None
    for e in events:
        if last_ts is None or e.timestamp > last_ts:
            last_ts = e.timestamp

    return ReflectionStats(
        total_events=total_events,
        last_timestamp=last_ts,
    )
