from us_core.core.orchestration import CoreOrchestrator


def test_orchestrator_register_and_heartbeat_order():
    orchestrator = CoreOrchestrator()
    call_log = []

    def step_a(ctx):
        call_log.append(("a", ctx["tick"]))
        return {"name": "a"}

    def step_b(ctx):
        call_log.append(("b", ctx["tick"]))
        return {"name": "b"}

    orchestrator.register_system("A", step_a)
    orchestrator.register_system("B", step_b)

    result = orchestrator.heartbeat({"tick": 1})

    assert set(result.keys()) == {"A", "B"}
    assert call_log == [("a", 1), ("b", 1)]


def test_orchestrator_enable_disable_system():
    orchestrator = CoreOrchestrator()
    calls = []

    def step(ctx):
        calls.append(True)
        return {}

    orchestrator.register_system("S", step, enabled=False)

    # disabled -> no calls
    orchestrator.heartbeat({})
    assert calls == []

    orchestrator.enable_system("S")
    orchestrator.heartbeat({})
    assert calls == [True]
