from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .mood import DailyMood, mood_label


@dataclass
class SelfCareSuggestion:
    """
    自我照顾建议（Phase 3-S01）：

    - mode: 建议模式
        - "rest": 以休息 / 降负为主
        - "balance": 以平衡为主（不多也不少）
        - "focus": 以专注 / 推进为主
    - message: 一段适合直接展示给用户的中文建议
    - average_mood: 最近若干天的平均情绪分数（-1 ~ 1）
    - days_considered: 纳入计算的天数
    """

    mode: str
    message: str
    average_mood: float
    days_considered: int


def build_self_care_suggestion(daily: List[DailyMood]) -> Optional[SelfCareSuggestion]:
    """
    根据最近几天的 DailyMood，给出一条「自我照顾建议」。

    规则（v0 简单版本）：
      - 只看最近最多 3 天的数据（如果天数不足则按实际为准）
      - 计算 average_mood = 这几天的 average_score 的平均
      - 分段：
          average_mood <= -0.4  -> mode="rest"
          -0.4 < average_mood < 0.2 -> mode="balance"
          average_mood >= 0.2  -> mode="focus"

    注意：这里不做任何「诊断」，只是基于当前情绪趋势给一点温柔的建议。
    """
    if not daily:
        return None

    # 取最近最多 3 天
    recent = daily[-3:]
    avg = sum(d.average_score for d in recent) / len(recent)
    avg = round(avg, 3)

    label = mood_label(avg)
    days_count = len(recent)

    if avg <= -0.4:
        mode = "rest"
        message = (
            f"这 {days_count} 天整体情绪是「{label}」，平均情绪分大约 {avg:+.2f}。"
            "最近你承受的压力不小，今天可以适当给自己放点水："
            "优先处理最重要的两三件小事，其它的先允许自己缓一缓，"
            "多补一点睡眠 / 喝水 / 简单走走，让神经系统有机会慢慢回到安全感里。"
        )
    elif avg < 0.2:
        mode = "balance"
        message = (
            f"这 {days_count} 天的情绪整体是「{label}」，平均情绪分大约 {avg:+.2f}。"
            "整体还在可承受范围，但时不时会有点起伏。"
            "今天可以在「照顾自己」和「推进重要事情」之间做个平衡："
            "给自己留出一小块完全不追求效率的时间，同时挑一件对你中长期重要的小事稳稳推进。"
        )
    else:
        mode = "focus"
        message = (
            f"这 {days_count} 天整体情绪是「{label}」，平均情绪分大约 {avg:+.2f}。"
            "说明你最近的状态整体还不错，也有一定的心理余裕。"
            "今天可以考虑安排一点对你来说「重要但有点挑战」的事情，"
            "比如推进宇宙奇点的一个小阶段，或者处理一个一直想解决的现实问题，"
            "同时也记得在专注之外给自己留一点放松的空间。"
        )

    return SelfCareSuggestion(
        mode=mode,
        message=message,
        average_mood=avg,
        days_considered=days_count,
    )
