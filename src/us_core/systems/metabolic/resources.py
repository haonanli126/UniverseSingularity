from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ResourceBudget:
    """代谢系统的资源预算（上限）。"""

    cpu: float
    memory: float
    attention: float
    energy: float


@dataclass
class ResourceUsage:
    """一次任务或当前的资源使用量。"""

    cpu: float = 0.0
    memory: float = 0.0
    attention: float = 0.0
    energy: float = 0.0


class ResourceManager:
    """
    资源管理器 v0：

    - 跟踪当前资源使用
    - 判断是否还能分配
    - 支持释放资源
    """

    def __init__(self, budget: ResourceBudget) -> None:
        self.budget = budget
        self.current_usage = ResourceUsage()

    def can_allocate(self, usage: ResourceUsage) -> bool:
        return (
            self.current_usage.cpu + usage.cpu <= self.budget.cpu
            and self.current_usage.memory + usage.memory <= self.budget.memory
            and self.current_usage.attention + usage.attention <= self.budget.attention
            and self.current_usage.energy + usage.energy <= self.budget.energy
        )

    def allocate(self, usage: ResourceUsage) -> bool:
        if not self.can_allocate(usage):
            return False
        self.current_usage.cpu += usage.cpu
        self.current_usage.memory += usage.memory
        self.current_usage.attention += usage.attention
        self.current_usage.energy += usage.energy
        return True

    def release(self, usage: ResourceUsage) -> None:
        # 防止出现负值
        self.current_usage.cpu = max(0.0, self.current_usage.cpu - usage.cpu)
        self.current_usage.memory = max(
            0.0, self.current_usage.memory - usage.memory
        )
        self.current_usage.attention = max(
            0.0, self.current_usage.attention - usage.attention
        )
        self.current_usage.energy = max(
            0.0, self.current_usage.energy - usage.energy
        )

    def utilization(self) -> Dict[str, float]:
        """返回各类资源的使用比例（0.0 ~ 1.0）。"""
        return {
            "cpu": 0.0
            if self.budget.cpu <= 0
            else self.current_usage.cpu / self.budget.cpu,
            "memory": 0.0
            if self.budget.memory <= 0
            else self.current_usage.memory / self.budget.memory,
            "attention": 0.0
            if self.budget.attention <= 0
            else self.current_usage.attention / self.budget.attention,
            "energy": 0.0
            if self.budget.energy <= 0
            else self.current_usage.energy / self.budget.energy,
        }
