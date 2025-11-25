from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np

from us_core.systems.environment.interface import (
    Environment,
    STATE_SIZE,
    NUM_ACTIONS,
    GridAction,
)

try:
    import pygame  # type: ignore
except ImportError:  # pragma: no cover - 测试环境不强制依赖 pygame
    pygame = None  # type: ignore


CellPos = Tuple[int, int]


# 网格编码约定：
# 0 = 空地
# 1 = 墙壁
# 2 = 钥匙
# 3 = 门
# 4 = 目标
# 5 = 角色（没有钥匙）
# 6 = 角色（拿着钥匙）
EMPTY = 0
WALL = 1
KEY = 2
DOOR = 3
GOAL = 4


@dataclass
class SimpleGridWorld(Environment):
    """10x10 网格世界环境（逻辑 + 渲染）。"""

    width: int = 10
    height: int = 10

    # 内部状态
    grid: np.ndarray = field(init=False)
    agent_pos: CellPos = field(init=False)
    _start_pos: CellPos = field(init=False)
    _goal_pos: CellPos = field(init=False)
    _key_pos: CellPos = field(init=False)
    _door_pos: CellPos = field(init=False)
    _has_key: bool = field(default=False, init=False)

    # pygame 相关
    _screen: Any = field(default=None, init=False)
    _clock: Any = field(default=None, init=False)
    _cell_size: int = 40

    @property
    def state_size(self) -> int:
        return STATE_SIZE

    @property
    def action_size(self) -> int:
        return NUM_ACTIONS

    # =====================
    # 环境核心逻辑
    # =====================

    def reset(self) -> np.ndarray:
        """重置环境，并返回 100 维状态向量。"""
        self._init_grid()
        self._start_pos = (1, 1)
        self.agent_pos = self._start_pos

        # 固定放置 key / door / goal
        self._key_pos = (1, self.width - 2)
        self._door_pos = (self.height // 2, self.width // 2)
        self._goal_pos = (self.height - 2, self.width - 2)

        self.grid[self._key_pos] = KEY
        self.grid[self._door_pos] = DOOR
        self.grid[self._goal_pos] = GOAL

        self._has_key = False
        return self._encode_state()

    def _init_grid(self) -> None:
        """初始化 10x10 网格和墙壁。"""
        g = np.zeros((self.height, self.width), dtype=np.int8)
        # 边界墙
        g[0, :] = WALL
        g[-1, :] = WALL
        g[:, 0] = WALL
        g[:, -1] = WALL

        # 简单内部障碍
        g[3, 2:8] = WALL
        g[6, 1:7] = WALL

        self.grid = g

    def step(self, action: int | GridAction) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """执行一步动作，返回 (next_state, reward, done, info)。"""
        if isinstance(action, int):
            action = GridAction(action)

        reward = -0.01  # 每步轻微惩罚，鼓励尽快到达目标
        done = False
        info: Dict[str, Any] = {}

        new_pos = self._next_position(action)
        cur_y, cur_x = self.agent_pos
        new_y, new_x = new_pos

        # 撞墙
        if self.grid[new_y, new_x] == WALL:
            reward -= 0.1
            info["collision"] = True
            # 不移动
            return self._encode_state(), reward, done, info

        # 门逻辑
        if (new_y, new_x) == self._door_pos:
            if not self._has_key:
                # 没有钥匙，门挡住
                reward -= 0.1
                info["door_blocked"] = True
                return self._encode_state(), reward, done, info
            else:
                # 有钥匙，开门并通过
                info["door_opened"] = True
                # 门变成空地
                self.grid[self._door_pos] = EMPTY

        # 移动成功
        self.agent_pos = (new_y, new_x)

        # 拾取钥匙
        if (new_y, new_x) == self._key_pos and not self._has_key:
            self._has_key = True
            self.grid[self._key_pos] = EMPTY
            reward += 0.2
            info["picked_key"] = True

        # 到达终点
        if (new_y, new_x) == self._goal_pos:
            reward += 1.0
            done = True
            info["reached_goal"] = True

        return self._encode_state(), reward, done, info

    def _next_position(self, action: GridAction) -> CellPos:
        y, x = self.agent_pos
        if action == GridAction.UP:
            return y - 1, x
        if action == GridAction.DOWN:
            return y + 1, x
        if action == GridAction.LEFT:
            return y, x - 1
        if action == GridAction.RIGHT:
            return y, x + 1
        # PICK_KEY / OPEN_DOOR 对位置不产生直接影响
        return y, x

    def _encode_state(self) -> np.ndarray:
        """将当前网格 + 角色状态编码为 100 维向量。"""
        g = self.grid.copy()

        ay, ax = self.agent_pos
        if self._has_key:
            g[ay, ax] = 6  # 角色 + 钥匙
        else:
            g[ay, ax] = 5  # 角色

        flat = g.astype(np.float32).reshape(-1)
        assert flat.shape == (STATE_SIZE,)
        # 测试中只要求 0~6 之间
        return flat

    # =====================
    # 渲染接口
    # =====================

    def render(self, mode: str = "ascii") -> Optional[str]:
        """渲染当前状态。

        mode="ascii"  -> 返回 ASCII 字符串（也会 print）
        mode="human"  -> 使用 pygame 在窗口中渲染（如果可用）
        """
        if mode == "ascii":
            ascii_map = self._render_ascii()
            print(ascii_map)
            return ascii_map

        if mode == "human":
            self._render_pygame()
            return None

        # 其他模式暂不支持
        return None

    def _render_ascii(self) -> str:
        """生成 ASCII 地图字符串。"""
        lines: list[str] = []
        for y in range(self.height):
            row_chars: list[str] = []
            for x in range(self.width):
                c = self._cell_to_char((y, x))
                row_chars.append(c)
            lines.append("".join(row_chars))
        return "\n".join(lines)

    def _cell_to_char(self, pos: CellPos) -> str:
        y, x = pos
        if pos == self.agent_pos:
            return "A"  # Agent

        val = self.grid[y, x]
        if val == WALL:
            return "#"
        if val == KEY:
            return "K"
        if val == DOOR:
            return "D"
        if val == GOAL:
            return "G"
        return "."  # EMPTY / 其他

    def _render_pygame(self) -> None:
        """使用 pygame 渲染网格（仅在本地手动调试时使用）。"""
        if pygame is None:  # pragma: no cover - 测试环境不走这里
            raise RuntimeError("pygame 未安装，无法使用 human 渲染模式。请运行 `pip install pygame`。")

        if self._screen is None:
            pygame.init()
            size = (self.width * self._cell_size, self.height * self._cell_size)
            self._screen = pygame.display.set_mode(size)
            pygame.display.set_caption("UniverseSingularity - SimpleGridWorld")
            self._clock = pygame.time.Clock()

        # 只负责画画，不处理事件（事件交给外部脚本）
        self._screen.fill((0, 0, 0))

        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * self._cell_size,
                    y * self._cell_size,
                    self._cell_size,
                    self._cell_size,
                )

                color = (30, 30, 30)  # 空地
                val = self.grid[y, x]
                if (y, x) == self.agent_pos:
                    color = (200, 200, 50)  # Agent
                elif val == WALL:
                    color = (80, 80, 80)
                elif val == KEY:
                    color = (50, 200, 50)
                elif val == DOOR:
                    color = (150, 75, 0)
                elif val == GOAL:
                    color = (200, 50, 50)

                pygame.draw.rect(self._screen, color, rect)
                pygame.draw.rect(self._screen, (40, 40, 40), rect, width=1)

        pygame.display.flip()
        if self._clock is not None:
            self._clock.tick(30)

    def close(self) -> None:
        """关闭 pygame 资源（如果已打开）。"""
        if pygame is not None and self._screen is not None:  # pragma: no cover
            pygame.display.quit()
            pygame.quit()
            self._screen = None
            self._clock = None
