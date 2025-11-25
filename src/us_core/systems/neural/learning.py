from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class Experience:
    """单条经验 (s, a, r, s', done)。"""

    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """经验回放缓冲区（简单实现）。"""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self._capacity = capacity
        self._buffer: List[Experience] = []
        self._position: int = 0

    def __len__(self) -> int:
        return len(self._buffer)

    def add(self, state: np.ndarray, action: int, reward: float,
            next_state: np.ndarray, done: bool) -> None:
        exp = Experience(
            state=state.astype(np.float32),
            action=int(action),
            reward=float(reward),
            next_state=next_state.astype(np.float32),
            done=bool(done),
        )
        if len(self._buffer) < self._capacity:
            self._buffer.append(exp)
        else:
            self._buffer[self._position] = exp
        self._position = (self._position + 1) % self._capacity

    def sample(self, batch_size: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if not self._buffer:
            raise ValueError("buffer is empty")

        idxs = np.random.choice(len(self._buffer), size=batch_size, replace=len(self._buffer) < batch_size)
        states = np.stack([self._buffer[i].state for i in idxs], axis=0)
        actions = np.array([self._buffer[i].action for i in idxs], dtype=np.int64)
        rewards = np.array([self._buffer[i].reward for i in idxs], dtype=np.float32)
        next_states = np.stack([self._buffer[i].next_state for i in idxs], axis=0)
        dones = np.array([self._buffer[i].done for i in idxs], dtype=np.bool_)

        return states, actions, rewards, next_states, dones
