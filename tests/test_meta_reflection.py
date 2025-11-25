import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.meta.reflection import (
    PatternAnalyzer,
    BiasDetector,
    ImprovementSuggester,
)


def test_pattern_analyzer_rolling_success_and_setback():
    analyzer = PatternAnalyzer()
    outcomes = [True, True, False, False]
    rates = analyzer.rolling_success_rate(outcomes, window=2)
    # True -> 1.0, (1+1)/2 -> 1.0, (1+0)/2 -> 0.5, (0+0)/2 -> 0.0
    assert rates[0] == 1.0
    assert rates[1] == 1.0
    assert rates[2] == 0.5
    assert rates[3] == 0.0

    # 明显回落：前半段全 True，后半段全 False
    outcomes = [True, True, True, False, False, False]
    assert analyzer.detect_setback(outcomes, threshold=0.3) is True


def test_bias_detector_overconfidence_gap():
    detector = BiasDetector()
    # 高信心但准确率低 -> 过度自信 gap > 0
    predictions = [
        (0.9, False),
        (0.8, False),
        (0.7, True),
    ]
    gap = detector.overconfidence_gap(predictions)
    assert gap > 0.3


def test_improvement_suggester_generates_actions():
    suggester = ImprovementSuggester()
    actions = suggester.suggest_actions(overconfidence_gap=0.5)
    assert any("自信" in a or "信心" in a for a in actions)
