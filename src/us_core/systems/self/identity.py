from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass(order=True)
class LifeEvent:
    """一条自传体记忆事件。"""

    timestamp: datetime
    description: str
    tags: List[str] = field(default_factory=list)
    emotional_valence: float = 0.0  # [-1, 1] 之间：负面 ~ 正面


@dataclass
class AutobiographicalMemory:
    """自传体记忆容器，负责存储和简单检索。"""

    _events: List[LifeEvent] = field(default_factory=list)

    def add_event(self, event: LifeEvent) -> None:
        self._events.append(event)
        # 保持按时间排序
        self._events.sort(key=lambda e: e.timestamp)

    def recent_events(self, limit: int = 10) -> List[LifeEvent]:
        """返回最近的若干条事件（按时间升序）。"""
        if limit < 0:
            return list(self._events)
        return list(self._events[-limit:])

    def events_by_tag(self, tag: str) -> List[LifeEvent]:
        """按标签过滤事件。"""
        tag_lower = tag.lower()
        return [
            e
            for e in self._events
            if any(t.lower() == tag_lower for t in e.tags)
        ]

    def stats(self) -> Dict[str, float]:
        """返回简单的情绪分布统计。"""
        if not self._events:
            return {"count": 0.0, "positive_ratio": 0.0}
        positives = sum(1 for e in self._events if e.emotional_valence >= 0)
        total = len(self._events)
        return {"count": float(total), "positive_ratio": positives / float(total)}


@dataclass
class SelfNarrative:
    """根据自传体记忆生成一个非常简洁的自我故事摘要。"""

    def summarise(self, memory: AutobiographicalMemory) -> str:
        events = memory.recent_events(50)
        if not events:
            return "暂无自传体记忆。"

        stats = memory.stats()
        lines: List[str] = []

        lines.append(f"共有 {int(stats['count'])} 条关键经历被记录。")

        if stats["positive_ratio"] >= 0.6:
            tone = "整体基调偏积极、成长型。"
        elif stats["positive_ratio"] <= 0.4:
            tone = "整体基调略显艰难，但仍在前进。"
        else:
            tone = "经历中既有起伏也有收获。"
        lines.append(tone)

        first = events[0]
        last = events[-1]
        lines.append(f"从「{first.description}」一路走到「{last.description}」。")

        return "\n".join(lines)


@dataclass
class SelfIdentity:
    """
    自我身份模型：记录核心特质 + 最近一次基于记忆的自我总结。
    """

    core_traits: List[str] = field(default_factory=list)
    last_updated: datetime | None = None
    last_summary: str | None = None

    def update_from_memory(self, memory: AutobiographicalMemory) -> None:
        """
        根据自传体记忆更新自我身份。
        这里用一个非常简化、但可测试的规则：
        - 正向情绪比例高 -> 增加 'resilient'
        - 出现 care 标签 -> 增加 'caring'
        """
        stats = memory.stats()
        events = memory.recent_events(50)

        traits = set(self.core_traits)

        if stats["positive_ratio"] > 0.6:
            traits.add("resilient")

        if any("care" in " ".join(e.tags).lower() for e in events):
            traits.add("caring")

        self.core_traits = sorted(traits)
        self.last_updated = datetime.utcnow()
        self.last_summary = SelfNarrative().summarise(memory)
