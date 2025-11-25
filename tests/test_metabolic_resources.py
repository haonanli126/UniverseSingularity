from us_core.systems.metabolic.resources import (
    ResourceBudget,
    ResourceUsage,
    ResourceManager,
)


def test_resource_manager_allocation_and_release():
    budget = ResourceBudget(cpu=10.0, memory=100.0, attention=1.0, energy=50.0)
    manager = ResourceManager(budget)

    usage1 = ResourceUsage(cpu=3.0, memory=30.0, attention=0.5, energy=10.0)
    assert manager.can_allocate(usage1) is True
    assert manager.allocate(usage1) is True

    util = manager.utilization()
    assert 0.29 < util["cpu"] < 0.31  # 3/10
    assert 0.29 < util["memory"] < 0.31  # 30/100

    # 过量请求应该失败
    big_usage = ResourceUsage(cpu=100.0, memory=0.0, attention=0.0, energy=0.0)
    assert manager.allocate(big_usage) is False

    # 释放后使用率应下降
    manager.release(usage1)
    util2 = manager.utilization()
    assert util2["cpu"] < util["cpu"]
    assert util2["memory"] < util["memory"]
