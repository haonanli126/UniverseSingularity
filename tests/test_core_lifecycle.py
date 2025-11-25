import pytest

from us_core.core.orchestration import CoreOrchestrator
from us_core.core.lifecycle import LifecycleManager, LifecycleState


def test_lifecycle_happy_path():
    orchestrator = CoreOrchestrator()
    seen = []

    def step(ctx):
        seen.append(ctx["tick"])
        return {"tick": ctx["tick"]}

    orchestrator.register_system("test", step)
    manager = LifecycleManager(orchestrator)

    assert manager.state == LifecycleState.CREATED

    manager.initialize()
    assert manager.state == LifecycleState.INITIALIZED

    result = manager.step({"tick": 1})
    assert manager.state == LifecycleState.RUNNING
    assert manager.heartbeat_count == 1
    assert result["test"]["tick"] == 1
    assert seen == [1]

    manager.shutdown()
    assert manager.state == LifecycleState.STOPPED


def test_step_without_initialize_raises():
    orchestrator = CoreOrchestrator()
    manager = LifecycleManager(orchestrator)

    with pytest.raises(RuntimeError):
        manager.step({})
