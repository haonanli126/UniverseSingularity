import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.endocrine.reward import (
    RewardComponents,
    combine_rewards,
    discount_return,
)
from us_core.systems.endocrine.motivation import IntrinsicMotivationSignal


def test_combine_rewards_basic():
    intrinsic = IntrinsicMotivationSignal(
        curiosity=0.5,
        mastery=0.2,
        consistency=0.3,
    )

    components = combine_rewards(extrinsic=1.0, intrinsic_total=intrinsic.total)

    assert isinstance(components, RewardComponents)
    # default intrinsic_weight is 0.1
    assert components.extrinsic == 1.0
    expected_intrinsic = intrinsic.total * 0.1
    assert components.intrinsic == expected_intrinsic
    assert components.total == components.extrinsic + components.intrinsic


def test_discount_return_monotonic_with_gamma():
    rewards = [1.0, 1.0, 1.0]

    g_low = discount_return(rewards, gamma=0.5)
    g_high = discount_return(rewards, gamma=0.9)

    # higher gamma => future rewards matter more
    assert g_high > g_low
