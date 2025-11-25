from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional


@dataclass
class SkillStat:
    """简单的 Beta 分布技能统计：用成功/失败次数估计掌握度。"""

    alpha: float = 1.0  # 类似「成功次数 + 1」
    beta: float = 1.0  # 类似「失败次数 + 1」

    def update(self, success: bool) -> None:
        if success:
            self.alpha += 1.0
        else:
            self.beta += 1.0

    @property
    def competence(self) -> float:
        """返回技能掌握度估计值，范围 [0, 1]."""
        total = self.alpha + self.beta
        if total <= 0:
            return 0.0
        return self.alpha / total


@dataclass
class AbilityModel:
    """能力模型：记录自己在不同技能上的掌握度。"""

    skills: Dict[str, SkillStat] = field(default_factory=dict)

    def _get_stat(self, skill: str) -> SkillStat:
        if skill not in self.skills:
            self.skills[skill] = SkillStat()
        return self.skills[skill]

    def update(self, skill: str, success: bool) -> None:
        """根据一次成功/失败结果更新技能掌握度。"""
        self._get_stat(skill).update(success)

    def get_competence(self, skill: str) -> float:
        """获取某个技能当前的掌握度估计。"""
        return self._get_stat(skill).competence

    def as_dict(self) -> Dict[str, float]:
        """导出当前所有技能的掌握度快照。"""
        return {name: stat.competence for name, stat in self.skills.items()}


@dataclass
class ValueSystem:
    """价值系统：维护一组核心价值观及其权重（0~1）。"""

    values: Dict[str, float] = field(default_factory=dict)

    def __init__(self, initial_values: Optional[Dict[str, float]] = None) -> None:
        self.values = {}
        if initial_values:
            for k, v in initial_values.items():
                self.set_value(k, v)

    def _clip(self, weight: float) -> float:
        return float(max(0.0, min(1.0, weight)))

    def set_value(self, name: str, weight: float) -> None:
        """直接设置某个价值观重要性（会自动裁剪到 [0, 1]）。"""
        self.values[name] = self._clip(weight)

    def get_value(self, name: str, default: float = 0.5) -> float:
        """获取某个价值观权重，如不存在则初始化为 default。"""
        if name not in self.values:
            self.values[name] = self._clip(default)
        return self.values[name]

    def merge_feedback(self, feedback: Dict[str, float], lr: float = 0.1) -> None:
        """
        根据外部反馈调整价值权重，lr 控制变化速度。
        feedback: {value_name: target_weight}
        """
        for k, target in feedback.items():
            target = self._clip(target)
            current = self.get_value(k)
            updated = current + lr * (target - current)
            self.values[k] = self._clip(updated)


@dataclass
class PreferenceModel:
    """偏好模型：用简单的增量更新方式学习对不同选项的偏好。"""

    _scores: Dict[str, float] = field(default_factory=dict)

    def score(self, option: str, default: float = 0.0) -> float:
        return self._scores.get(option, default)

    def update_preference(self, option: str, reward: float, alpha: float = 0.1) -> None:
        """
        根据一次 reward 更新偏好。
        这是一个极简 Q-learning 形式：new = old + alpha * (reward - old)
        """
        old = self._scores.get(option, 0.0)
        new = old + alpha * (reward - old)
        self._scores[option] = new

    def best_option(self, options: Iterable[str]) -> Optional[str]:
        """在给定选项中选出当前偏好最高的那个。"""
        best_name: Optional[str] = None
        best_score: float = float("-inf")
        for opt in options:
            s = self.score(opt)
            if s > best_score:
                best_score = s
                best_name = opt
        return best_name


@dataclass
class SelfKnowledge:
    """
    自我知识总线：把能力模型、价值系统、偏好模型统一一个接口。
    """

    ability_model: AbilityModel = field(default_factory=AbilityModel)
    value_system: ValueSystem = field(default_factory=ValueSystem)
    preference_model: PreferenceModel = field(default_factory=PreferenceModel)

    def ability_confidence(self, skill: str) -> float:
        """查询自己在某个技能上的信心/掌握度。"""
        return self.ability_model.get_competence(skill)

    def value_weight(self, name: str) -> float:
        """查询某个价值观当前权重。"""
        return self.value_system.get_value(name)

    def best_option(self, options: Iterable[str]) -> Optional[str]:
        """在多个行为选项中，选择当前自我偏好最高的一个。"""
        return self.preference_model.best_option(list(options))
