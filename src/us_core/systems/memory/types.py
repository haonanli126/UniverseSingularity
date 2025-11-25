# src/us_core/systems/memory/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List


@dataclass(frozen=True)
class EpisodicMemory:
    """情景记忆：带时间戳的具体经历"""

    id: str
    timestamp: datetime
    content: str
    emotion_tags: List[str] = field(default_factory=list)
    importance: float = 0.5  # 0~1
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_added_emotion(self, tag: str) -> "EpisodicMemory":
        """返回一个新增情绪标签后的新实例（保持不可变风格）"""
        if tag in self.emotion_tags:
            return self
        new_tags = [*self.emotion_tags, tag]
        return EpisodicMemory(
            id=self.id,
            timestamp=self.timestamp,
            content=self.content,
            emotion_tags=new_tags,
            importance=self.importance,
            metadata=dict(self.metadata),
        )


@dataclass(frozen=True)
class SemanticMemory:
    """语义记忆：抽象知识"""

    id: str
    key: str
    value: str
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProceduralMemory:
    """程序记忆：技能 / 操作序列"""

    id: str
    name: str
    steps: List[str]

    def length(self) -> int:
        return len(self.steps)


class WorkingMemory:
    """工作记忆：小容量、短期缓冲，FIFO 结构"""

    def __init__(self, capacity: int = 7) -> None:
        self.capacity = max(1, capacity)
        self._items: List[Any] = []

    def add(self, item: Any) -> None:
        self._items.append(item)
        # 超出容量则丢弃最早的
        overflow = len(self._items) - self.capacity
        if overflow > 0:
            self._items = self._items[overflow:]

    def items(self) -> List[Any]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
