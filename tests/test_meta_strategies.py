import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.meta.strategies import StrategyLibrary


def test_get_by_kind_returns_learning_strategies():
    lib = StrategyLibrary()
    learning = lib.get_by_kind("learning")
    assert learning
    names = {s.name for s in learning}
    assert "deep_processing" in names or "spaced_repetition" in names


def test_suggest_for_high_difficulty_prefers_problem_solving():
    lib = StrategyLibrary()
    strategies = lib.suggest_for(difficulty="high", time_pressure="low")
    kinds = {s.kind for s in strategies}
    assert "problem_solving" in kinds
