from us_core.systems.immune.monitoring import (
    SystemHealthSnapshot,
    HealthMonitor,
)


def test_health_monitor_reports_healthy_and_unhealthy():
    monitor = HealthMonitor(
        latency_threshold=500.0,
        error_rate_threshold=0.05,
        cpu_threshold=0.9,
        memory_threshold=0.9,
    )

    # 健康快照
    monitor.add_snapshot(
        SystemHealthSnapshot(
            latency_ms=100.0,
            error_rate=0.0,
            cpu_usage=0.3,
            memory_usage=0.4,
        )
    )
    healthy = monitor.get_health_status()
    assert healthy.is_healthy is True
    assert healthy.score > 0.7

    # 不健康快照
    monitor.add_snapshot(
        SystemHealthSnapshot(
            latency_ms=2000.0,
            error_rate=0.2,
            cpu_usage=0.99,
            memory_usage=0.99,
        )
    )
    unhealthy = monitor.get_health_status()
    assert unhealthy.is_healthy is False
    assert unhealthy.score < healthy.score
    assert any(
        "latency" in r.lower() or "错误" in r for r in unhealthy.reasons
    )
