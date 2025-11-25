from us_core.systems.metabolic.resources import ResourceBudget, ResourceUsage
from us_core.systems.metabolic.optimization import ResourceOptimizer


def test_resource_optimizer_scales_budget_based_on_history():
    current = ResourceBudget(cpu=10.0, memory=100.0, attention=1.0, energy=50.0)
    history = [
        ResourceUsage(cpu=5.0, memory=60.0, attention=0.3, energy=20.0),
        ResourceUsage(cpu=8.0, memory=80.0, attention=0.5, energy=30.0),
    ]

    optimizer = ResourceOptimizer()
    new_budget = optimizer.suggest_budget(history, current)

    # 不会缩到太离谱
    assert new_budget.cpu > 0
    assert new_budget.cpu >= current.cpu * 0.8
    assert new_budget.cpu <= current.cpu * 1.5

    assert new_budget.memory >= current.memory * 0.8
    assert new_budget.memory <= current.memory * 1.5
