from us_core.systems.immune.monitoring import HealthStatus
from us_core.systems.immune.protection import ProtectionController


def test_protection_controller_triggers_emergency_on_low_score():
    controller = ProtectionController(health_threshold=0.7)

    healthy = HealthStatus(is_healthy=True, score=0.9, reasons=[])
    unhealthy = HealthStatus(is_healthy=False, score=0.3, reasons=["error"])

    controller.evaluate_and_act(healthy)
    assert controller.emergency_stop_activated is False

    controller.evaluate_and_act(unhealthy)
    assert controller.emergency_stop_activated is True


def test_protection_controller_isolates_components():
    controller = ProtectionController()

    assert controller.is_component_isolated("neural") is False
    controller.isolate_component("neural")
    assert controller.is_component_isolated("neural") is True
    controller.release_component("neural")
    assert controller.is_component_isolated("neural") is False
