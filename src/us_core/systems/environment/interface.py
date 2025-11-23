from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Dict, Tuple

import numpy as np


#: 标准状态空间：10x10 展平 → 100 维向量
STATE_SIZE: int = 100

#: 标准动作空间：6 个基础动作
NUM_ACTIONS: int = 6


class GridAction(IntEnum):
    """标准网格世界动作定义。"""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    PICK_KEY = 4
    OPEN_DOOR = 5


class Environment(ABC):
    """所有环境实现需要遵守的基础接口。"""

    @property
    def state_size(self) -> int:
        return STATE_SIZE

    @property
    def action_size(self) -> int:
        return NUM_ACTIONS

    @abstractmethod
    def reset(self) -> np.ndarray:
        """重置环境并返回初始状态向量。"""
        raise NotImplementedError

    @abstractmethod
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """执行一步动作。

        返回: (next_state, reward, done, info)
        """
        raise NotImplementedError

    def render(self, mode: str = "ascii") -> None:
        """可选的渲染方法，默认不做任何事情。"""
        return
