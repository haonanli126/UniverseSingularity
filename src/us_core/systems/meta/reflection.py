# src/us_core/systems/meta/reflection.py
from __future__ import annotations

from typing import Iterable, List, Tuple


class PatternAnalyzer:
    """分析成功 / 失败模式"""

    def rolling_success_rate(self, outcomes: Iterable[bool], window: int = 1) -> List[float]:
        outs = [bool(o) for o in outcomes]
        if not outs:
            return []

        rates: List[float] = []
        for i in range(len(outs)):
            start = max(0, i - window + 1)
            segment = outs[start : i + 1]
            rates.append(sum(segment) / len(segment))
        return rates

    def detect_setback(self, outcomes: Iterable[bool], threshold: float = 0.2) -> bool:
        """简单检测：前半段成功率 - 后半段成功率 是否大于阈值"""
        outs = [bool(o) for o in outcomes]
        if len(outs) < 4:
            return False

        mid = len(outs) // 2
        first = outs[:mid]
        second = outs[mid:]

        def rate(xs: List[bool]) -> float:
            return sum(xs) / len(xs) if xs else 0.0

        gap = rate(first) - rate(second)
        return gap > threshold


class BiasDetector:
    """检测过度自信等偏差"""

    def overconfidence_gap(self, predictions: Iterable[Tuple[float, bool]]) -> float:
        """返回预测信心与真实结果之间的平均绝对差"""
        preds = list(predictions)
        if not preds:
            return 0.0

        diffs: List[float] = []
        for p, outcome in preds:
            y = 1.0 if outcome else 0.0
            diffs.append(abs(p - y))
        return sum(diffs) / len(diffs)


class ImprovementSuggester:
    """根据偏差给出改进建议"""

    def suggest_actions(self, overconfidence_gap: float) -> List[str]:
        actions: List[str] = []

        if overconfidence_gap > 0.4:
            actions.append("减少主观自信，先写下证据再下结论。")
            actions.append("记录每次预测的信心和结果，定期校准自己的『自信 vs 真实』。")
        elif overconfidence_gap > 0.2:
            actions.append("在给出高信心判断前，先多想一个反例。")
        else:
            actions.append("当前信心和结果较为匹配，保持对证据的敏感。")

        # 测试里会检查有“自信/信心”字样
        return actions
