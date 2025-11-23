from __future__ import annotations

import sys
from pathlib import Path

# 确保 src 在 sys.path 中，这样可以 import us_core
ROOT = Path(__file__).resolve().parents[1]  # -> D:\UniverseSingularity
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from us_core.environments.grid_world import SimpleGridWorld  # noqa: E402
from us_core.systems.environment.interface import (  # noqa: E402
    STATE_SIZE,
    NUM_ACTIONS,
    Environment,
    GridAction,
)
from us_core.utils.visualization import episode_reward_stats  # noqa: E402
from us_core.utils.monitoring import measure_step_throughput  # noqa: E402


def test_reset_returns_state_vector_with_correct_size_and_bounds():
    env = SimpleGridWorld()
    state = env.reset()

    assert isinstance(state, np.ndarray)
    assert state.shape == (STATE_SIZE,)
    # 所有编码应在 0~6 范围内（含 agent 编码）
    assert state.min() >= 0.0
    assert state.max() <= 6.0


def test_step_moves_agent_when_no_wall():
    env = SimpleGridWorld()
    env.reset()
    # 初始点 (1,1)，右侧为可行走区域
    orig_pos = env.agent_pos
    next_state, reward, done, info = env.step(GridAction.RIGHT)

    assert env.agent_pos != orig_pos
    assert env.agent_pos[0] == orig_pos[0]
    assert env.agent_pos[1] == orig_pos[1] + 1
    assert not done
    assert isinstance(next_state, np.ndarray)


def test_collision_with_wall_does_not_move_and_penalizes():
    env = SimpleGridWorld()
    env.reset()
    # 靠近上边界，向上移动会撞墙
    env.agent_pos = (1, 1)
    orig_pos = env.agent_pos

    _, reward, _, info = env.step(GridAction.UP)

    assert env.agent_pos == orig_pos
    assert reward < 0.0
    assert info.get("collision", False) is True


def test_reaching_goal_gives_positive_reward_and_done():
    env = SimpleGridWorld()
    env.reset()

    gy, gx = env._goal_pos  # type: ignore[attr-defined]
    # 把 agent 放在目标左侧一格，确保下一步可以到达目标
    env.agent_pos = (gy, gx - 1)

    _, reward, done, info = env.step(GridAction.RIGHT)

    assert done is True
    assert reward > 0.0
    assert info.get("reached_goal", False) is True


def test_interface_constants_and_action_space():
    env = SimpleGridWorld()
    assert isinstance(env, Environment)
    assert env.state_size == STATE_SIZE
    assert env.action_size == NUM_ACTIONS

    # 检查 GridAction 枚举值
    assert int(GridAction.UP) == 0
    assert int(GridAction.DOWN) == 1
    assert int(GridAction.LEFT) == 2
    assert int(GridAction.RIGHT) == 3
    assert int(GridAction.PICK_KEY) == 4
    assert int(GridAction.OPEN_DOOR) == 5


def test_visualization_and_monitoring_helpers_run():
    stats = episode_reward_stats([1.0, -0.5, 0.5])
    assert stats["total"] == pytest.approx(1.0)
    assert stats["length"] == pytest.approx(3.0)
    assert "mean" in stats

    throughput = measure_step_throughput(lambda: None, num_steps=10)
    assert throughput > 0.0

