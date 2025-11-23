from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from ..systems.environment.interface import (
    Environment,
    GridAction,
    STATE_SIZE,
)


class CellType(IntEnum):
    EMPTY = 0
    WALL = 1
    KEY = 2
    DOOR_CLOSED = 3
    DOOR_OPEN = 4
    GOAL = 5


@dataclass
class SimpleGridWorld(Environment):
    """一个简单的 10x10 网格世界环境。

    - 外围一圈是墙；
    - 内部有：钥匙、门、目标点；
    - agent 可以移动、捡钥匙、开门，到达目标即完成。
    """

    width: int = 10
    height: int = 10
    max_steps: int = 200

    def __post_init__(self) -> None:
        if self.width * self.height != STATE_SIZE:
            raise ValueError("SimpleGridWorld must be 10x10 for STATE_SIZE=100")

        self._build_default_map()
        self.reset()

    # --- 环境构建 & 重置 ---

    def _build_default_map(self) -> None:
        """构建静态地图布局。"""
        grid = np.zeros((self.height, self.width), dtype=np.int8)

        # 外围一圈墙
        grid[0, :] = CellType.WALL
        grid[-1, :] = CellType.WALL
        grid[:, 0] = CellType.WALL
        grid[:, -1] = CellType.WALL

        # 关键元素位置
        self._start_pos: Tuple[int, int] = (1, 1)   # 起点
        self._key_pos: Tuple[int, int] = (1, 3)     # 钥匙
        self._door_pos: Tuple[int, int] = (5, 5)    # 门
        self._goal_pos: Tuple[int, int] = (8, 8)    # 目标

        grid[self._key_pos] = CellType.KEY
        grid[self._door_pos] = CellType.DOOR_CLOSED
        grid[self._goal_pos] = CellType.GOAL

        self._base_grid = grid

    def reset(self) -> np.ndarray:
        """重置环境到初始状态。"""
        self._grid = self._base_grid.copy()
        self.agent_pos: Tuple[int, int] = self._start_pos
        self.has_key: bool = False
        self.door_open: bool = False
        self.step_count: int = 0
        self.done: bool = False
        return self._get_state()

    # --- 内部辅助方法 ---

    def _in_bounds(self, pos: Tuple[int, int]) -> bool:
        y, x = pos
        return 0 <= y < self.height and 0 <= x < self.width

    def _is_blocked(self, pos: Tuple[int, int]) -> bool:
        """是否被墙或关闭的门阻挡。"""
        if not self._in_bounds(pos):
            return True
        cell = self._grid[pos]
        if cell == CellType.WALL:
            return True
        if (pos == self._door_pos) and not self.door_open:
            return True
        return False

    def _adjacent_to(self, target: Tuple[int, int]) -> bool:
        ay, ax = self.agent_pos
        ty, tx = target
        return abs(ay - ty) + abs(ax - tx) == 1

    def _encode_grid_with_agent(self) -> np.ndarray:
        """将静态地图 + agent 状态编码成 10x10 整型网格。"""
        grid = self._grid.copy()

        # 门状态
        if self.door_open:
            grid[self._door_pos] = CellType.DOOR_OPEN
        else:
            grid[self._door_pos] = CellType.DOOR_CLOSED

        # 钥匙若已拾取则不再显示
        if self.has_key and grid[self._key_pos] == CellType.KEY:
            grid[self._key_pos] = CellType.EMPTY

        # agent 覆盖当前位置
        ay, ax = self.agent_pos
        grid[ay, ax] = 6  # 6 单独表示 agent

        return grid

    def _get_state(self) -> np.ndarray:
        """返回展平后的 100 维状态向量。"""
        grid = self._encode_grid_with_agent()
        flat = grid.astype(np.float32).flatten()
        assert flat.shape[0] == STATE_SIZE
        return flat

    # --- 主交互 API ---

    def step(
        self,
        action: Union[int, GridAction],
    ) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """执行一步动作。"""

        if isinstance(action, GridAction):
            a = int(action)
        else:
            a = int(action)

        info: Dict[str, Any] = {}

        # 若已经结束，保持状态不变
        if getattr(self, "done", False):
            return self._get_state(), 0.0, True, {"already_done": True}

        self.step_count += 1
        reward = -0.01  # 小的时间步惩罚，鼓励尽快完成

        # 处理动作
        if a in (GridAction.UP, GridAction.DOWN, GridAction.LEFT, GridAction.RIGHT):
            dy, dx = 0, 0
            if a == GridAction.UP:
                dy = -1
            elif a == GridAction.DOWN:
                dy = 1
            elif a == GridAction.LEFT:
                dx = -1
            elif a == GridAction.RIGHT:
                dx = 1

            ny = self.agent_pos[0] + dy
            nx = self.agent_pos[1] + dx
            new_pos = (ny, nx)

            if self._is_blocked(new_pos):
                # 撞墙 / 撞门，轻微惩罚
                reward -= 0.04
                info["collision"] = True
            else:
                self.agent_pos = new_pos

        elif a == GridAction.PICK_KEY:
            # 若站在钥匙格子上且未持有，拾取成功
            if (not self.has_key) and (self.agent_pos == self._key_pos):
                self.has_key = True
                reward += 0.5
                self._grid[self._key_pos] = CellType.EMPTY
                info["picked_key"] = True
            else:
                reward -= 0.02
                info["picked_key"] = False

        elif a == GridAction.OPEN_DOOR:
            if self.has_key and (not self.door_open) and self._adjacent_to(self._door_pos):
                self.door_open = True
                self._grid[self._door_pos] = CellType.DOOR_OPEN
                reward += 0.5
                info["door_opened"] = True
            else:
                reward -= 0.02
                info["door_opened"] = False
        else:
            # 未定义动作
            reward -= 0.05
            info["invalid_action"] = True

        # 到达目标
        if self.agent_pos == self._goal_pos:
            reward += 1.0
            self.done = True
            info["reached_goal"] = True

        # 超过最大步数自动结束
        if self.step_count >= self.max_steps and not getattr(self, "done", False):
            self.done = True
            info["truncated"] = True

        return self._get_state(), reward, self.done, info

    # --- 渲染 ---

    def render(self, mode: str = "ascii") -> None:
        """渲染当前状态。

        - mode="ascii": 在终端用字符渲染；
        - mode="pygame": 尝试用 pygame 渲染（懒加载，若未安装则报友好提示）。
        """
        if mode == "ascii":
            self._render_ascii()
        elif mode == "pygame":
            self._render_pygame()
        else:
            raise ValueError(f"Unsupported render mode: {mode!r}")

    def _render_ascii(self) -> None:
        grid = self._encode_grid_with_agent()
        char_map = {
            CellType.EMPTY: " . ",
            CellType.WALL: "###",
            CellType.KEY: " K ",
            CellType.DOOR_CLOSED: "[ ]",
            CellType.DOOR_OPEN: " | ",
            CellType.GOAL: " G ",
        }

        for y in range(self.height):
            row_str = ""
            for x in range(self.width):
                if (y, x) == self.agent_pos:
                    row_str += " A "
                else:
                    val = grid[y, x]
                    if val == 6:
                        row_str += " A "
                    else:
                        row_str += char_map.get(CellType(val), " ? ")
            print(row_str)
        print()

    def _render_pygame(self) -> None:
        """使用 pygame 渲染（若未安装 pygame，则抛出 RuntimeError）。"""
        try:
            import os
            import pygame  # type: ignore
        except ImportError as exc:  # pragma: no cover - 依赖外部库
            raise RuntimeError("pygame is not installed") from exc

        # 适配无窗口环境
        if "SDL_VIDEODRIVER" not in os.environ:
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        cell_size = 32
        width_px = self.width * cell_size
        height_px = self.height * cell_size

        pygame.init()
        screen = pygame.display.set_mode((width_px, height_px))
        pygame.display.set_caption("SimpleGridWorld")

        grid = self._encode_grid_with_agent()

        colors = {
            CellType.EMPTY: (30, 30, 30),
            CellType.WALL: (80, 80, 80),
            CellType.KEY: (255, 215, 0),
            CellType.DOOR_CLOSED: (160, 82, 45),
            CellType.DOOR_OPEN: (205, 133, 63),
            CellType.GOAL: (50, 205, 50),
            "agent": (70, 130, 180),
        }

        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                if (y, x) == self.agent_pos:
                    color = colors["agent"]
                else:
                    val = grid[y, x]
                    if val == 6:
                        color = colors["agent"]
                    else:
                        color = colors.get(CellType(val), (255, 0, 0))
                pygame.draw.rect(screen, color, rect)

        pygame.display.flip()
