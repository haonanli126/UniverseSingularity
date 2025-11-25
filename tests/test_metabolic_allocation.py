from us_core.systems.metabolic.resources import (
    ResourceBudget,
    ResourceUsage,
    ResourceManager,
)
from us_core.systems.metabolic.allocation import PriorityTask, ResourceAllocator


def test_resource_allocator_prefers_high_priority_tasks():
    budget = ResourceBudget(cpu=10.0, memory=100.0, attention=1.0, energy=50.0)
    manager = ResourceManager(budget)
    allocator = ResourceAllocator(manager)

    small_cost = ResourceUsage(cpu=2.0, memory=10.0, attention=0.1, energy=5.0)
    big_cost = ResourceUsage(cpu=9.0, memory=90.0, attention=0.9, energy=40.0)

    low_priority = PriorityTask(name="low", priority=0.1, cost=big_cost)
    high_priority = PriorityTask(name="high", priority=0.9, cost=small_cost)

    selected = allocator.select_executable_tasks([low_priority, high_priority])
    names = [t.name for t in selected]

    # 高优先级任务一定会被选中，并且排在第一位
    assert "high" in names
    assert names[0] == "high"
    # 由于资源不足，低优先级的大任务不会被执行
    assert "low" not in names
