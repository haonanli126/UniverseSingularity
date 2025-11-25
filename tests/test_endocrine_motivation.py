import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.endocrine.motivation import (
    IntrinsicMotivationConfig,
    IntrinsicMotivationSignal,
    compute_intrinsic_motivation,
)


def test_compute_intrinsic_motivation_basic():
    signal = compute_intrinsic_motivation(
        prediction_error=0.5,
        skill_progress=0.2,
        cognitive_dissonance=0.3,
    )

    assert isinstance(signal, IntrinsicMotivationSignal)
    assert signal.curiosity == 0.5
    assert signal.mastery == 0.2
    # consistency uses (1 - dissonance)
    assert signal.consistency == 0.7
    assert 0.0 <= signal.total <= 3.0


def test_compute_intrinsic_motivation_respects_weights():
    config = IntrinsicMotivationConfig(
        curiosity_weight=2.0,
        mastery_weight=0.5,
        consistency_weight=1.0,
    )

    signal = compute_intrinsic_motivation(
        prediction_error=0.6,
        skill_progress=0.6,
        cognitive_dissonance=0.5,
        config=config,
    )

    # curiosity: 0.6 * 2.0 = 1.2 -> clamped to 1.0
    assert signal.curiosity == 1.0
    # mastery: 0.6 * 0.5 = 0.3
    assert signal.mastery == 0.3
    # consistency: (1 - 0.5) * 1.0 = 0.5
    assert signal.consistency == 0.5


def test_compute_intrinsic_motivation_clamps_inputs():
    signal = compute_intrinsic_motivation(
        prediction_error=-1.0,
        skill_progress=2.0,
        cognitive_dissonance=2.0,
    )

    assert 0.0 <= signal.curiosity <= 1.0
    assert 0.0 <= signal.mastery <= 1.0
    assert 0.0 <= signal.consistency <= 1.0
