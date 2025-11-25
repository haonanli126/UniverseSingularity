from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# 确保 src 在 sys.path 中
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.environments.grid_world import SimpleGridWorld  # noqa: E402
from us_core.utils.visualization import ascii_from_state  # noqa: E402


def test_env_render_ascii_returns_map_with_agent():
    env = SimpleGridWorld()
    env.reset()

    ascii_map = env.render(mode="ascii")
    assert isinstance(ascii_map, str)
    lines = ascii_map.splitlines()
    assert len(lines) == env.height
    # 至少应该有一个 Agent 字符
    assert any("A" in line for line in lines)


def test_ascii_from_state_matches_shape_and_contains_chars():
    # 构造一个简单的状态：中间一个 Agent，右下角一个目标
    grid = np.zeros((10, 10), dtype=np.float32)
    grid[5, 5] = 5  # Agent
    grid[8, 8] = 4  # Goal
    state = grid.reshape(-1)

    ascii_map = ascii_from_state(state)
    assert "A" in ascii_map
    assert "G" in ascii_map
    assert len(ascii_map.splitlines()) == 10
