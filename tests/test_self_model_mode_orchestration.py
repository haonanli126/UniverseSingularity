from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.self_model.insights import PlannerInsights, TagStats  # type: ignore
from us_core.self_model.mode_orchestration import decide_day_mode  # type: ignore


def _make_insights(total_events: int, overall_rate: float, tags: list[TagStats]) -> PlannerInsights:
    return PlannerInsights(
        total_tasks=len(tags),
        total_planned_events=total_events,
        total_completed_events=int(total_events * overall_rate),
        overall_completion_rate=overall_rate,
        tag_stats=tags,
    )


def test_decide_day_mode_no_history_falls_back_to_mood():
    insights = _make_insights(
        total_events=0,
        overall_rate=0.0,
        tags=[],
    )

    decision = decide_day_mode(mood_mode="focus", insights=insights)

    assert decision.final_mode == "focus"
    assert decision.self_model_mode is None
    assert "完全听情绪系统" in decision.reason


def test_decide_day_mode_strong_conflict_uses_balance():
    # 构造一个总体表现建议 rest 的自我模型（整体完成率很低）
    tags = [
        TagStats(tag="self-care", times_planned=5, times_completed=1),
        TagStats(tag="universe", times_planned=5, times_completed=1),
    ]
    insights = _make_insights(
        total_events=10,
        overall_rate=0.2,
        tags=tags,
    )

    decision = decide_day_mode(mood_mode="focus", insights=insights)

    # 自我模型会推荐 rest，而情绪是 focus → strong conflict → balance
    assert decision.mood_mode == "focus"
    assert decision.self_model_mode == "rest"
    assert decision.final_mode == "balance"


def test_decide_day_mode_agreement_uses_that_mode():
    tags = [
        TagStats(tag="self-care", times_planned=3, times_completed=3),   # 高完成率
        TagStats(tag="universe", times_planned=3, times_completed=2),
    ]
    insights = _make_insights(
        total_events=6,
        overall_rate=0.85,  # overall 高 → 自我模型推荐 focus
        tags=tags,
    )

    decision = decide_day_mode(mood_mode="focus", insights=insights)

    assert decision.self_model_mode == "focus"
    assert decision.final_mode == "focus"
    assert "判断一致" in decision.reason
