from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Action:
    """表示一个待执行的动作，用于安全评估。"""

    name: str
    risk_level: float  # 0.0 ~ 1.0 之间的风险评分，越高越危险
    description: str = ""


@dataclass
class ActionSafetyReport:
    """动作安全性评估结果。"""

    is_safe: bool
    risk_score: float
    reasons: List[str]


class ActionSafetyFilter:
    """
    动作安全过滤器：基于风险分数和阈值进行简单判定。

    这只是一个轻量级 v0 版本，未来可以接入更复杂的规则系统。
    """

    def __init__(self, risk_threshold: float = 0.7) -> None:
        self.risk_threshold = risk_threshold

    def evaluate(self, action: Action) -> ActionSafetyReport:
        # 将风险分数裁剪到 [0, 1]
        risk_score = max(0.0, min(1.0, action.risk_level))
        is_safe = risk_score <= self.risk_threshold
        reasons: List[str] = []
        if not is_safe:
            reasons.append("动作风险评分高于阈值")
        return ActionSafetyReport(is_safe=is_safe, risk_score=risk_score, reasons=reasons)


@dataclass
class GoalAlignmentReport:
    """目标与核心价值观的一致性检查结果。"""

    is_aligned: bool
    alignment_score: float  # 0.0 ~ 1.0
    violated_values: List[str]


class GoalAlignmentFilter:
    """
    目标对齐过滤器：基于简单的关键词规则判断是否违反安全价值观。

    之后可以替换为更复杂的规则引擎或语言模型评估。
    """

    def __init__(self, core_values: Optional[List[str]] = None) -> None:
        self.core_values = core_values or ["safety", "respect", "honesty"]
        # 一些明显不安全/不符合价值观的关键词（只是示例）
        self._banned_keywords = ["harm", "伤害", "欺骗", "欺诈"]

    def evaluate(self, goal_description: str) -> GoalAlignmentReport:
        text = goal_description.lower()
        violated: List[str] = []
        for kw in self._banned_keywords:
            if kw in text:
                violated.append(kw)

        is_aligned = not violated
        # 非常粗糙的打分：有违规就降到 0.2
        alignment_score = 1.0 if is_aligned else 0.2
        return GoalAlignmentReport(
            is_aligned=is_aligned,
            alignment_score=alignment_score,
            violated_values=violated,
        )


@dataclass
class ResourceLimits:
    """资源上限配置，用于安全检查。"""

    max_cpu: float
    max_memory: float


@dataclass
class ResourceSafetyReport:
    """资源使用情况是否在安全范围内。"""

    within_limits: bool
    cpu_ratio: float
    memory_ratio: float


class ResourceSafetyFilter:
    """简单的资源使用安全过滤器。"""

    def __init__(self, limits: ResourceLimits) -> None:
        self.limits = limits

    def evaluate(self, usage_cpu: float, usage_memory: float) -> ResourceSafetyReport:
        cpu_ratio = (
            usage_cpu / self.limits.max_cpu if self.limits.max_cpu > 0 else 0.0
        )
        memory_ratio = (
            usage_memory / self.limits.max_memory if self.limits.max_memory > 0 else 0.0
        )
        within_limits = cpu_ratio <= 1.0 and memory_ratio <= 1.0
        return ResourceSafetyReport(
            within_limits=within_limits,
            cpu_ratio=cpu_ratio,
            memory_ratio=memory_ratio,
        )
