from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .networks import PolicyNetwork, WorldModel


@dataclass
class EpsilonGreedyPolicy:
    """ε-贪婪动作选择器。"""

    policy_net: PolicyNetwork
    action_size: int
    epsilon: float = 0.1

    def select_action(self, state: np.ndarray, rng: Optional[np.random.Generator] = None) -> tuple[int, float]:
        if rng is None:
            rng = np.random.default_rng()

        if state.ndim == 1:
            state = state[None, :]

        # 探索 or 利用
        if rng.random() < self.epsilon:
            action = int(rng.integers(0, self.action_size))
            confidence = 1.0 / float(self.action_size)
            return action, float(confidence)

        # 贪婪选择
        logits = self.policy_net.forward(state)[0]  # (action_size,)
        # softmax 得到一个“信心”感
        max_logit = float(np.max(logits))
        exp = np.exp(logits - max_logit)
        probs = exp / np.sum(exp)
        action = int(np.argmax(probs))
        confidence = float(probs[action])
        return action, confidence


@dataclass
class SimplePlanner:
    """极简 3 步前瞻规划模块（stub 版本）。

    当前实现：
    - 对给定起始状态，尝试若干随机动作序列
    - 使用 WorldModel rollout 预测未来奖励“分数”
    - 返回得分最高的第一步动作
    """

    world_model: WorldModel
    action_size: int
    horizon: int = 3
    num_samples: int = 16

    def plan(self, state: np.ndarray, rng: Optional[np.random.Generator] = None) -> int:
        if rng is None:
            rng = np.random.default_rng()
        if state.ndim == 1:
            state = state[None, :]

        best_action = 0
        best_score = -1e9

        for _ in range(self.num_samples):
            # 随机采样一个动作序列
            actions = rng.integers(0, self.action_size, size=self.horizon)
            s = state.copy()
            score = 0.0
            for a in actions:
                s = self.world_model.predict_next_state(s, int(a))
                # 这里用一个非常简化的“奖励”：状态向量的 L2 范数
                score += float(np.linalg.norm(s))

            if score > best_score:
                best_score = score
                best_action = int(actions[0])

        return best_action
