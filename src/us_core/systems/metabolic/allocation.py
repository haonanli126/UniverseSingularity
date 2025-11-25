from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .resources import ResourceUsage, ResourceManager


@dataclass
class PriorityTask:
    """带优先级的任务，用于资源分配决策。"""

    name: str
    priority: float  # 0.0 ~ 1.0，越高越重要
    cost: ResourceUsage


class ResourceAllocator:
    """
    资源分配器 v0：

    - 根据优先级从高到低尝试选择一批可执行任务
    - 一旦资源不足，就跳过该任务（不做回溯）
    """

    def __init__(self, manager: ResourceManager) -> None:
        self.manager = manager

    def select_executable_tasks(self, tasks: List[PriorityTask]) -> List[PriorityTask]:
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        selected: List[PriorityTask] = []
        for task in sorted_tasks:
            if self.manager.can_allocate(task.cost):
                self.manager.allocate(task.cost)
                selected.append(task)
        return selected
