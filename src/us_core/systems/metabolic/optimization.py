from __future__ import annotations

from typing import List

from .resources import ResourceUsage, ResourceBudget


class ResourceOptimizer:
    """
    简单的资源预算优化器 v0：

    - 根据历史使用情况，建议一个新的预算
    - 规则：不小于 0.8 * 当前预算，不大于 1.5 * 当前预算
    - 同时尝试覆盖历史峰值的 1.2 倍
    """

    def suggest_budget(
        self,
        history: List[ResourceUsage],
        current: ResourceBudget,
    ) -> ResourceBudget:
        # 没有历史就保持现状
        if not history:
            return current

        max_cpu = max(u.cpu for u in history)
        max_memory = max(u.memory for u in history)
        max_attention = max(u.attention for u in history)
        max_energy = max(u.energy for u in history)

        def adjust(current_val: float, max_used: float) -> float:
            # 目标值：历史最大使用量的 1.2 倍，至少是当前预算的 0.8 倍
            target = max(max_used * 1.2, current_val * 0.8)
            lower = current_val * 0.5
            upper = current_val * 1.5
            # 限制在 [0.5x, 1.5x] 区间内
            return max(lower, min(upper, target))

        return ResourceBudget(
            cpu=adjust(current.cpu, max_cpu),
            memory=adjust(current.memory, max_memory),
            attention=adjust(current.attention, max_attention),
            energy=adjust(current.energy, max_energy),
        )
