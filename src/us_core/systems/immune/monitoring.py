from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, List


@dataclass
class SystemHealthSnapshot:
    """某一时刻的系统健康快照。"""

    latency_ms: float
    error_rate: float  # 0.0 ~ 1.0
    cpu_usage: float  # 0.0 ~ 1.0
    memory_usage: float  # 0.0 ~ 1.0


@dataclass
class HealthStatus:
    """基于最近快照计算出的整体健康状态。"""

    is_healthy: bool
    score: float  # 0.0 ~ 1.0
    reasons: List[str]


class HealthMonitor:
    """
    免疫系统的健康监控器 v0 版。

    - 当前实现：使用最后一个快照进行规则判断
    - 未来可以扩展：滑动窗口平均、趋势分析等
    """

    def __init__(
        self,
        max_history: int = 100,
        latency_threshold: float = 500.0,
        error_rate_threshold: float = 0.05,
        cpu_threshold: float = 0.9,
        memory_threshold: float = 0.9,
    ) -> None:
        self._history: Deque[SystemHealthSnapshot] = deque(maxlen=max_history)
        self.latency_threshold = latency_threshold
        self.error_rate_threshold = error_rate_threshold
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def add_snapshot(self, snapshot: SystemHealthSnapshot) -> None:
        self._history.append(snapshot)

    def get_health_status(self) -> HealthStatus:
        # 没有数据时，认为健康但打一个标记原因
        if not self._history:
            return HealthStatus(is_healthy=True, score=1.0, reasons=["no data"])

        s = self._history[-1]
        score = 1.0
        reasons: List[str] = []

        if s.latency_ms > self.latency_threshold:
            score -= 0.3
            reasons.append("latency 高于阈值")
        if s.error_rate > self.error_rate_threshold:
            score -= 0.3
            reasons.append("错误率过高")
        if s.cpu_usage > self.cpu_threshold:
            score -= 0.2
            reasons.append("CPU 使用率过高")
        if s.memory_usage > self.memory_threshold:
            score -= 0.2
            reasons.append("内存使用率过高")

        score = max(0.0, min(1.0, score))
        is_healthy = score >= 0.7
        return HealthStatus(is_healthy=is_healthy, score=score, reasons=reasons)
