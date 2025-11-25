from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple

import numpy as np


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


@dataclass
class MLP:
    """简单的全连接前馈网络（只用于前向推理，不做训练）。"""

    layer_sizes: Sequence[int]
    _weights: List[np.ndarray] = field(init=False)
    _biases: List[np.ndarray] = field(init=False)

    def __post_init__(self) -> None:
        if len(self.layer_sizes) < 2:
            raise ValueError("layer_sizes 至少包含 input 和 output 大小")
        self._weights = []
        self._biases = []
        rng = np.random.default_rng()
        for in_dim, out_dim in zip(self.layer_sizes[:-1], self.layer_sizes[1:]):
            w = rng.normal(0.0, 0.1, size=(in_dim, out_dim)).astype(np.float32)
            b = np.zeros(out_dim, dtype=np.float32)
            self._weights.append(w)
            self._biases.append(b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        if x.ndim == 1:
            x = x[None, :]
        h = x.astype(np.float32)
        for i, (w, b) in enumerate(zip(self._weights, self._biases)):
            h = h @ w + b
            if i < len(self._weights) - 1:
                h = _relu(h)
        return h


@dataclass
class PolicyNetwork:
    """策略网络：从状态向量 -> 动作偏好（logits）。"""

    input_size: int
    output_size: int
    hidden_sizes: Tuple[int, int, int] = (256, 128, 64)
    _mlp: MLP = field(init=False)

    def __post_init__(self) -> None:
        layer_sizes: Tuple[int, ...] = (self.input_size, *self.hidden_sizes, self.output_size)
        self._mlp = MLP(layer_sizes=layer_sizes)

    def forward(self, state: np.ndarray) -> np.ndarray:
        return self._mlp.forward(state)


@dataclass
class ValueNetwork:
    """价值网络：从状态向量 -> 标量价值。"""

    input_size: int
    hidden_sizes: Tuple[int, int, int] = (256, 128, 32)
    _mlp: MLP = field(init=False)

    def __post_init__(self) -> None:
        layer_sizes: Tuple[int, ...] = (self.input_size, *self.hidden_sizes, 1)
        self._mlp = MLP(layer_sizes=layer_sizes)

    def forward(self, state: np.ndarray) -> np.ndarray:
        return self._mlp.forward(state)  # (batch, 1)


@dataclass
class FeatureExtractor:
    """特征提取网络：将高维状态映射到较小的特征空间。"""

    input_size: int
    feature_dim: int = 32
    _mlp: MLP = field(init=False)

    def __post_init__(self) -> None:
        self._mlp = MLP(layer_sizes=(self.input_size, 64, self.feature_dim))

    def forward(self, state: np.ndarray) -> np.ndarray:
        return self._mlp.forward(state)


@dataclass
class WorldModel:
    """简化版世界模型。

    输入：当前状态 + 动作 one-hot
    输出：预测的下一状态增量（delta），并与当前状态相加作为下一状态估计。
    """

    state_dim: int
    num_actions: int
    _mlp: MLP = field(init=False)

    def __post_init__(self) -> None:
        input_dim = self.state_dim + self.num_actions
        self._mlp = MLP(layer_sizes=(input_dim, 128, self.state_dim))

    def _concat_state_action(self, state: np.ndarray, action: int) -> np.ndarray:
        if state.ndim == 1:
            state = state[None, :]
        batch = state.shape[0]
        one_hot = np.zeros((batch, self.num_actions), dtype=np.float32)
        one_hot[:, action] = 1.0
        return np.concatenate([state, one_hot], axis=1)

    def predict_next_state(self, state: np.ndarray, action: int) -> np.ndarray:
        sa = self._concat_state_action(state, action)
        delta = self._mlp.forward(sa)
        if state.ndim == 1:
            state = state[None, :]
        return state + delta
