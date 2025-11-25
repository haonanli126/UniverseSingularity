from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from .monitoring import HealthStatus


@dataclass
class ProtectionController:
    """
    保护机制控制器 v0：

    - 根据 HealthStatus 触发紧急停止（emergency stop）
    - 支持对特定组件进行隔离 / 解除隔离
    """

    health_threshold: float = 0.7
    emergency_stop_activated: bool = False
    isolated_components: Set[str] = field(default_factory=set)

    def evaluate_and_act(self, health_status: HealthStatus) -> None:
        """
        根据健康状态决定是否触发紧急停止。
        规则：分数低于阈值 或 标记为不健康 -> 触发。
        """
        if (not health_status.is_healthy) or (health_status.score < self.health_threshold):
            self.activate_emergency_stop()

    def activate_emergency_stop(self) -> None:
        self.emergency_stop_activated = True

    # --- 组件隔离相关 ---

    def isolate_component(self, name: str) -> None:
        self.isolated_components.add(name)

    def release_component(self, name: str) -> None:
        self.isolated_components.discard(name)

    def is_component_isolated(self, name: str) -> bool:
        return name in self.isolated_components
