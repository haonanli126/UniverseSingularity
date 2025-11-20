from __future__ import annotations

"""
最简单的短时记忆：环形缓冲区。

- 用来存最近一批事件（默认 1000 条）
- 超出容量时，丢弃最早的事件
"""

from typing import List

from .events import EmbryoEvent


class MemoryBuffer:
    def __init__(self, max_events: int = 1000) -> None:
        if max_events <= 0:
            raise ValueError("max_events 必须是正整数")
        self._max_events = max_events
        self._events: List[EmbryoEvent] = []

    @property
    def max_events(self) -> int:
        return self._max_events

    def add(self, event: EmbryoEvent) -> None:
        """加入一条新事件，必要时丢弃最旧的一条。"""
        self._events.append(event)
        if len(self._events) > self._max_events:
            # 丢弃最旧的
            self._events.pop(0)

    def all(self) -> List[EmbryoEvent]:
        """返回所有事件的副本（避免外部随意修改内部列表）。"""
        return list(self._events)

    def last(self, n: int = 1) -> List[EmbryoEvent]:
        """获取最近 n 条事件。"""
        if n <= 0:
            return []
        return self._events[-n:]
