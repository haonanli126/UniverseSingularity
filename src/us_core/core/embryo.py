from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from us_core.systems.consciousness.global_workspace import GlobalWorkspaceSystem
from .orchestration import CoreOrchestrator
from .lifecycle import LifecycleManager
from .monitoring import PerformanceMetrics


@dataclass
class ConsciousDigitalEmbryo:
    """
    数字胚胎的高层封装：

    把 4 个核心部件打包在一起：
    - workspace: 全局工作空间系统
    - orchestrator: 中枢调度器
    - lifecycle: 生命周期管理器
    - metrics: 性能 / 心跳监控
    - context: 当前“全局上下文”
    - heartbeat_count: 记录调用 heartbeat 的次数
    """
    workspace: GlobalWorkspaceSystem
    orchestrator: CoreOrchestrator
    lifecycle: LifecycleManager
    metrics: PerformanceMetrics
    context: Dict[str, Any] = field(default_factory=dict)
    heartbeat_count: int = 0

    @classmethod
    def simple_demo(cls) -> "ConsciousDigitalEmbryo":
        """
        创建一个用于测试 / Demo 的简易胚胎实例：

        - GlobalWorkspaceSystem：默认实例
        - CoreOrchestrator：默认实例
        - LifecycleManager：注入 orchestrator
        - PerformanceMetrics：默认实例
        - context：从一个空 dict 开始
        - heartbeat_count：从 0 开始
        """
        workspace = GlobalWorkspaceSystem()
        orchestrator = CoreOrchestrator()
        lifecycle = LifecycleManager(orchestrator=orchestrator)
        metrics = PerformanceMetrics()

        embryo = cls(
            workspace=workspace,
            orchestrator=orchestrator,
            lifecycle=lifecycle,
            metrics=metrics,
            context={},
            heartbeat_count=0,
        )
        return embryo

    def heartbeat(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行一次“心跳”：

        测试期望的行为：
        - 接收一个外部的 context dict
        - 返回一个 *新的* context（不要直接改传入的那个）
        - 在其中维护 `heartbeat_steps` 计数器
        - 同时递增自身的 `heartbeat_count`

        在此基础上，再尽量调用 lifecycle / orchestrator / metrics
        上可能存在的心跳相关方法（如果存在的话）。
        """
        # 1) 复制一份上下文，避免直接修改传入的 dict
        base_ctx: Dict[str, Any] = dict(context or {})
        base_ctx.setdefault("heartbeat_steps", 0)
        base_ctx["heartbeat_steps"] += 1

        # 2) 更新自身计数 & 当前上下文
        self.heartbeat_count += 1
        self.context = base_ctx

        # 3) 尝试驱动生命周期管理器
        if hasattr(self.lifecycle, "heartbeat"):
            try:
                # 优先尝试接受 context 的版本
                result = self.lifecycle.heartbeat(base_ctx)  # type: ignore[arg-type]
                # 如果 lifecycle.heartbeat 返回了新的上下文，则更新之
                if isinstance(result, dict):
                    base_ctx = result
                    self.context = base_ctx
            except TypeError:
                # 不接受参数的版本
                self.lifecycle.heartbeat()  # type: ignore[call-arg]
        elif hasattr(self.lifecycle, "tick"):
            try:
                self.lifecycle.tick(base_ctx)  # type: ignore[arg-type]
            except TypeError:
                self.lifecycle.tick()  # type: ignore[call-arg]

        # 4) 尝试让 orchestrator 跑一次循环（如果它提供了类似方法）
        if hasattr(self.orchestrator, "run_cycle"):
            try:
                self.orchestrator.run_cycle(base_ctx)  # type: ignore[arg-type]
            except TypeError:
                self.orchestrator.run_cycle()  # type: ignore[call-arg]
        elif hasattr(self.orchestrator, "run_once"):
            try:
                self.orchestrator.run_once(base_ctx)  # type: ignore[arg-type]
            except TypeError:
                self.orchestrator.run_once()  # type: ignore[call-arg]

        # 5) 记录一次心跳到 metrics
        if hasattr(self.metrics, "record_heartbeat"):
            try:
                self.metrics.record_heartbeat()
            except TypeError:
                self.metrics.record_heartbeat(base_ctx)  # type: ignore[call-arg]

        # 6) 返回最新上下文（测试会用这个）
        return base_ctx
