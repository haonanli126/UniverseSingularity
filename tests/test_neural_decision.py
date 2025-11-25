from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.neural.decision import EpsilonGreedyPolicy, SimplePlanner  # noqa: E402
from us_core.systems.neural.networks import PolicyNetwork, WorldModel  # noqa: E402


def test_epsilon_greedy_policy_with_low_epsilon_prefers_greedy():
    # 使用一个可控的 policy_net：让 forward 输出固定 logits
    class DummyPolicy(PolicyNetwork):
        def __init__(self):
            pass

        def forward(self, state: np.ndarray) -> np.ndarray:
            # 动作 2 最高
            return np.array([[0.0, 1.0, 5.0, 0.5, -1.0, 0.0]], dtype=np.float32)

    policy = DummyPolicy()
    eg = EpsilonGreedyPolicy(policy_net=policy, action_size=6, epsilon=0.0)

    rng = np.random.default_rng(123)
    action, confidence = eg.select_action(np.zeros(100, dtype=np.float32), rng=rng)
    assert action == 2
    assert 0.0 <= confidence <= 1.0


def test_epsilon_greedy_policy_with_high_epsilon_explores():
    class DummyPolicy(PolicyNetwork):
        def __init__(self):
            pass

        def forward(self, state: np.ndarray) -> np.ndarray:
            return np.zeros((1, 6), dtype=np.float32)

    policy = DummyPolicy()
    eg = EpsilonGreedyPolicy(policy_net=policy, action_size=6, epsilon=1.0)

    rng = np.random.default_rng(42)
    actions = {eg.select_action(np.zeros(100, dtype=np.float32), rng=rng)[0] for _ in range(20)}
    # 高 epsilon 下，至少应看到多个不同动作
    assert len(actions) > 1


def test_simple_planner_returns_valid_action():
    wm = WorldModel(state_dim=100, num_actions=6)
    planner = SimplePlanner(world_model=wm, action_size=6, horizon=3, num_samples=8)

    state = np.zeros(100, dtype=np.float32)
    rng = np.random.default_rng(7)
    action = planner.plan(state, rng=rng)

    assert 0 <= action < 6
