from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.self_model.insights import PlannerInsights, TagStats  # type: ignore
from us_core.self_model.mode_orchestration import ModeDecision  # type: ignore
from us_core.self_model.narrative import build_daily_self_story  # type: ignore


def _make_insights(total_events: int, overall_rate: float, tags: list[TagStats]) -> PlannerInsights:
    return PlannerInsights(
        total_tasks=len(tags),
        total_planned_events=total_events,
        total_completed_events=int(total_events * overall_rate),
        overall_completion_rate=overall_rate,
        tag_stats=tags,
    )


def test_build_daily_self_story_no_history_mentions_empty_state():
    insights = _make_insights(total_events=0, overall_rate=0.0, tags=[])
    decision = ModeDecision(
        mood_mode="focus",
        self_model_mode=None,
        final_mode="focus",
        reason="no history yet",
    )

    md = build_daily_self_story(decision, insights)

    assert "Daily Self Story: Planner Perspective" in md
    assert "final_mode: **focus**" in md
    assert "还没有任何执行历史" in md


def test_build_daily_self_story_includes_best_and_worst_tags():
    tags = [
        TagStats(tag="universe", times_planned=3, times_completed=1),   # 33%
        TagStats(tag="self-care", times_planned=3, times_completed=3),  # 100%
    ]
    insights = _make_insights(total_events=6, overall_rate=0.5, tags=tags)
    decision = ModeDecision(
        mood_mode="rest",
        self_model_mode="focus",
        final_mode="balance",
        reason="conflict, use balance",
    )

    md = build_daily_self_story(
        decision,
        insights,
        top_n=2,
        min_planned_per_tag=1,
    )

    # 基本头部信息
    assert "final_mode: **balance**" in md
    assert "mood_mode: **rest**" in md
    assert "self_model_mode: **focus**" in md

    # 标签信息
    assert "`self-care`" in md
    assert "`universe`" in md

    # 强项 / 阻力段落标题
    assert "What I tend to finish" in md
    assert "What I keep postponing" in md
