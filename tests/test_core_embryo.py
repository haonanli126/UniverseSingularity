from us_core.core.embryo import ConsciousDigitalEmbryo
from us_core.core.lifecycle import LifecycleManager
from us_core.core.monitoring import PerformanceMetrics
from us_core.core.orchestration import CoreOrchestrator
from us_core.systems.consciousness.global_workspace import GlobalWorkspaceSystem


def test_simple_demo_creates_valid_embryo():
    embryo = ConsciousDigitalEmbryo.simple_demo()

    assert isinstance(embryo.workspace, GlobalWorkspaceSystem)
    assert isinstance(embryo.orchestrator, CoreOrchestrator)
    assert isinstance(embryo.lifecycle, LifecycleManager)
    assert isinstance(embryo.metrics, PerformanceMetrics)
    assert embryo.heartbeat_count == 0


def test_heartbeat_updates_counter_and_context():
    embryo = ConsciousDigitalEmbryo.simple_demo()

    ctx = {}
    ctx1 = embryo.heartbeat(ctx)

    # 心跳计数应该 +1
    assert embryo.heartbeat_count == 1
    # 上下文里应该记录我们的 “heartbeat_steps”
    assert ctx1["heartbeat_steps"] == 1

    ctx2 = embryo.heartbeat(ctx1)
    assert embryo.heartbeat_count == 2
    assert ctx2["heartbeat_steps"] == 2
