from __future__ import annotations

from typing import Dict, Sequence


def episode_reward_stats(rewards: Sequence[float]) -> Dict[str, float]:
    """对一条 episode 的奖励序列做简单统计。

    返回:
        {
            "total": 总奖励,
            "mean": 平均奖励,
            "length": 序列长度
        }
    """
    total = float(sum(rewards))
    length = len(rewards)
    mean = total / length if length > 0 else 0.0
    return {"total": total, "mean": mean, "length": float(length)}
