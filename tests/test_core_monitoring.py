from us_core.core.monitoring import PerformanceMetrics
from us_core.systems.consciousness.global_workspace import GlobalWorkspaceSystem


class DummyEmbryo:
    def __init__(self) -> None:
        self.learning_history = [0.0, 1.0]
        self.experience_usage = [1.0, 1.0]
        self.decision_accuracy = [0.5, 0.75]
        self.global_workspace = GlobalWorkspaceSystem()


def test_performance_metrics_basic_and_consciousness_level():
    embryo = DummyEmbryo()

    # 先让 global_workspace 产生一个 winner
    inputs = {
        "sensory": {
            "content": "hello",
            "newness": 1.0,
            "relevance": 1.0,
            "affect": 1.0,
            "goal_alignment": 1.0,
        }
    }
    embryo.global_workspace.compete_and_broadcast(inputs)

    metrics = PerformanceMetrics.calculate_all_metrics(embryo)

    # 关键指标都要存在
    assert PerformanceMetrics.LEARNING_EFFICIENCY in metrics
    assert PerformanceMetrics.SAMPLE_EFFICIENCY in metrics
    assert PerformanceMetrics.DECISION_ACCURACY in metrics
    assert PerformanceMetrics.CONSCIOUSNESS_LEVEL in metrics

    # learning_efficiency = mean([0,1]) = 0.5
    assert metrics[PerformanceMetrics.LEARNING_EFFICIENCY] == 0.5
    # sample_efficiency = mean([1,1]) = 1.0
    assert metrics[PerformanceMetrics.SAMPLE_EFFICIENCY] == 1.0
    # consciousness_level 在 [0,1]
    level = metrics[PerformanceMetrics.CONSCIOUSNESS_LEVEL]
    assert 0.0 <= level <= 1.0
