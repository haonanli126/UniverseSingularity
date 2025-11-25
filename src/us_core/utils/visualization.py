from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def episode_reward_stats(rewards: Sequence[float]) -> Dict[str, float]:
    """对一条 episode 的奖励做简单统计，用于日志/监控。"""
    arr = np.asarray(list(rewards), dtype=float)
    if arr.size == 0:
        return {"total": 0.0, "length": 0.0, "mean": 0.0}

    total = float(arr.sum())
    length = float(arr.size)
    mean = float(arr.mean())
    return {"total": total, "length": length, "mean": mean}


def ascii_from_state(state: np.ndarray) -> str:
    """从 100 维状态向量生成 10x10 ASCII 地图。

    约定与 SimpleGridWorld._encode_state 一致：
    0 = 空地
    1 = 墙壁
    2 = 钥匙
    3 = 门
    4 = 目标
    5 = 角色（无钥匙）
    6 = 角色（有钥匙）
    """
    if state.shape != (100,):
        raise ValueError(f"expected state shape (100,), got {state.shape}")

    grid = state.reshape(10, 10)
    lines: list[str] = []

    for y in range(10):
        row_chars: list[str] = []
        for x in range(10):
            v = int(grid[y, x])
            if v == 1:
                row_chars.append("#")
            elif v == 2:
                row_chars.append("K")
            elif v == 3:
                row_chars.append("D")
            elif v == 4:
                row_chars.append("G")
            elif v == 5 or v == 6:
                row_chars.append("A")
            else:
                row_chars.append(".")
        lines.append("".join(row_chars))

    return "\n".join(lines)
