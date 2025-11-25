# src/us_core/systems/memory/organization.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List
from collections import Counter, defaultdict
import re

from .types import EpisodicMemory, SemanticMemory


@dataclass
class AutobiographicalSlice:
    """时间区间内的一段自传体时间线"""

    episodes: List[EpisodicMemory]


class AutobiographicalOrganizer:
    """按时间组织情景记忆，形成自传体时间线"""

    def __init__(self) -> None:
        self._episodes: List[EpisodicMemory] = []

    def add(self, episode: EpisodicMemory) -> None:
        self._episodes.append(episode)
        # 始终按时间排序
        self._episodes.sort(key=lambda e: e.timestamp)

    def timeline(self) -> List[EpisodicMemory]:
        """返回完整时间线（从早到晚）"""
        return list(self._episodes)

    def between(self, start: datetime, end: datetime) -> AutobiographicalSlice:
        """取一个时间区间内的片段（包含边界）"""
        eps = [e for e in self._episodes if start <= e.timestamp <= end]
        return AutobiographicalSlice(episodes=eps)


class SchemaBuilder:
    """根据 tag 或 key 构建简单“图式”分组"""

    def build_schemas(
        self, memories: Iterable[SemanticMemory]
    ) -> Dict[str, List[SemanticMemory]]:
        schemas: Dict[str, List[SemanticMemory]] = {}

        for m in memories:
            # 优先按 tag 分组
            if m.tags:
                for tag in m.tags:
                    schemas.setdefault(tag, []).append(m)
            else:
                # 没有 tag 时，fallback 用 key 作为“图式名”
                schemas.setdefault(m.key, []).append(m)

        return schemas


class MemoryIndexer:
    """极简全文索引：按词频打分"""

    def __init__(self) -> None:
        # mem_id -> Counter(token -> freq)
        self._index: Dict[str, Counter[str]] = {}

    def _tokenize(self, text: str) -> List[str]:
        return [t for t in re.split(r"\W+", text.lower()) if t]

    def index(self, mem_id: str, text: str) -> None:
        tokens = self._tokenize(text)
        self._index[mem_id] = Counter(tokens)

    def search(self, query: str) -> List[str]:
        tokens = self._tokenize(query)
        scores: Dict[str, int] = defaultdict(int)

        for mem_id, counter in self._index.items():
            for t in tokens:
                scores[mem_id] += counter.get(t, 0)

        # 按得分从高到低排序，得分为 0 的直接剔除
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return [mem_id for mem_id, score in ranked if score > 0]
