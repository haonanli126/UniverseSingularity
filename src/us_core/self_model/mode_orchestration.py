from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .insights import PlannerInsights
from .recommendations import suggest_base_mode_from_insights


@dataclass
class ModeDecision:
    """情绪 + 自我模型联合决定一天基调的结果。"""

    mood_mode: str              # 情绪系统算出来的模式
    self_model_mode: Optional[str]  # 自我模型建议的模式（无历史时为 None）
    final_mode: str             # 最终推荐给 Planner 的模式
    reason: str                 # 人类可读解释


def _normalize_mode(mode: str) -> str:
    m = (mode or "balance").strip().lower()
    if m not in {"rest", "balance", "focus"}:
        return "balance"
    return m


def decide_day_mode(mood_mode: str, insights: PlannerInsights) -> ModeDecision:
    """综合情绪 + 执行自我画像，给出一天的 base_mode。

    策略大致是：

    - 没有任何历史记录：完全听情绪（mood_mode）；
    - 有历史：
        - 如果 mood_mode 和 self_model_mode 一致：直接用这个模式；
        - 如果冲突：
            * mood=focus, self=rest → final=balance（别硬刚也别躺平）；
            * mood=rest, self=focus → final=balance（身体说要休息，self 说你能打——那就折中）；
            * 其余：优先情绪，但在 reason 里提醒有偏差。
    """
    mood_mode_norm = _normalize_mode(mood_mode)

    # 无任何历史记录：退化为纯情绪模式
    if insights.total_planned_events == 0:
        return ModeDecision(
            mood_mode=mood_mode_norm,
            self_model_mode=None,
            final_mode=mood_mode_norm,
            reason="self-model 还没有任何执行历史记录，暂时完全听情绪系统的建议。",
        )

    self_model_mode = suggest_base_mode_from_insights(insights)
    self_model_mode_norm = _normalize_mode(self_model_mode)

    # 1) 完全一致：直接采用
    if mood_mode_norm == self_model_mode_norm:
        return ModeDecision(
            mood_mode=mood_mode_norm,
            self_model_mode=self_model_mode_norm,
            final_mode=mood_mode_norm,
            reason="情绪系统与自我模型对明天的节奏判断一致，可以放心采用这个模式。",
        )

    # 2) 典型强冲突：一个说 focus，一个说 rest → 折中为 balance
    pair = {mood_mode_norm, self_model_mode_norm}
    if pair == {"focus", "rest"}:
        return ModeDecision(
            mood_mode=mood_mode_norm,
            self_model_mode=self_model_mode_norm,
            final_mode="balance",
            reason=(
                "情绪和自我模型之间出现强冲突（一个想冲刺，一个想休息），"
                "建议把明天当成「调节节奏」的一天，用 balance 模式折中："
                "既安排少量关键推进任务，也留出明显的恢复空间。"
            ),
        )

    # 3) 其他轻度不一致：尊重情绪，但在解释里提醒偏差
    return ModeDecision(
        mood_mode=mood_mode_norm,
        self_model_mode=self_model_mode_norm,
        final_mode=mood_mode_norm,
        reason=(
            "情绪和自我模型对明天的节奏略有不同，这里优先尊重情绪系统的判断。"
            "可以在安排具体任务时稍微参考自我模型给出的标签完成率，避免把自己压得太满。"
        ),
    )
