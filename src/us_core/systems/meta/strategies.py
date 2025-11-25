# src/us_core/systems/meta/strategies.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Strategy:
    name: str
    kind: str          # "learning" / "thinking" / "problem_solving" 等
    description: str


class StrategyLibrary:
    """简单的策略库，用于根据场景挑选思维 / 学习策略"""

    def __init__(self) -> None:
        self._strategies: List[Strategy] = [
            Strategy(
                name="deep_processing",
                kind="learning",
                description="深度加工：用自己的话重述、举例、类比。",
            ),
            Strategy(
                name="spaced_repetition",
                kind="learning",
                description="间隔重复：分散在多次复习，而不是一次刷完。",
            ),
            Strategy(
                name="divide_and_conquer",
                kind="problem_solving",
                description="把大问题拆成多个小子问题逐个解决。",
            ),
            Strategy(
                name="backtracking",
                kind="problem_solving",
                description="探索多条路径，遇到死路就回退。",
            ),
        ]

    def get_by_kind(self, kind: str) -> List[Strategy]:
        kind = kind.lower()
        return [s for s in self._strategies if s.kind == kind]

    def suggest_for(self, difficulty: str, time_pressure: str) -> List[Strategy]:
        """根据难度 & 时间压力，给出几个候选策略"""
        difficulty = difficulty.lower()
        time_pressure = time_pressure.lower()

        result: List[Strategy] = []

        if difficulty == "high":
            # 高难度问题偏向 problem_solving
            result.extend(self.get_by_kind("problem_solving"))
        else:
            # 普通难度时，以 learning 策略为主
            result.extend(self.get_by_kind("learning"))

        # 时间压力高的话，保守选一到两个
        if time_pressure == "high" and len(result) > 2:
            result = result[:2]

        return result
