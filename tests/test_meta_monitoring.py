import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.meta.monitoring import (
    ThinkingMonitor,
    ConfidenceCalibrator,
    PerformanceTracker,
)


def test_thinking_monitor_logs_steps_in_order():
    monitor = ThinkingMonitor()
    s1 = monitor.log_step("first", decision="A", confidence=0.7)
    s2 = monitor.log_step("second", decision="B", confidence=0.8)

    assert s1.index == 0
    assert s2.index == 1

    monitor.set_outcome(0, True)
    monitor.set_outcome(1, False)

    steps = monitor.all_steps()
    assert [step.description for step in steps] == ["first", "second"]
    assert steps[0].outcome is True
    assert steps[1].outcome is False


def test_confidence_calibrator_brier_score():
    calibrator = ConfidenceCalibrator()
    calibrator.add_prediction(1.0, True)   # 误差 0
    calibrator.add_prediction(0.0, False)  # 误差 0
    assert calibrator.brier_score() == 0.0

    calibrator = ConfidenceCalibrator()
    calibrator.add_prediction(1.0, False)  # 误差 1
    assert calibrator.brier_score() == 1.0


def test_performance_tracker_moving_average():
    tracker = PerformanceTracker()
    for r in [1.0, 2.0, 3.0, 4.0]:
        tracker.add_episode_reward(r)

    ma = tracker.moving_average(window=2)
    # [1.0, (1+2)/2, (2+3)/2, (3+4)/2]
    assert ma[0] == 1.0
    assert ma[1] == 1.5
    assert ma[2] == 2.5
    assert ma[3] == 3.5

