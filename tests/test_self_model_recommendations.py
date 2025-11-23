from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.self_model.insights import PlannerInsights, TagStats  # type: ignore
from us_core.self_model.recommendations import (  # type: ignore
    build_self_model_recommendations,
    recommendations_to_markdown,
)


def test_build_self_model_recommendations_uses_tag_completion_rates():
    insights = PlannerInsights(
        total_tasks=2,
        total_planned_events=6,
        total_completed_events=4,
        overall_completion_rate=4 / 6,
        tag_stats=[
            TagStats(tag="self-care", times_planned=3, times_completed=1),  # 33%
            TagStats(tag="universe", times_planned=3, times_completed=3),   # 100%
        ],
    )

    rec = build_self_model_recommendations(
        insights,
        min_planned_per_tag=1,
        top_n=2,
    )

    strength_tags = [ts.tag for ts in rec.strength_tags]
    friction_tags = [ts.tag for ts in rec.friction_tags]

    # 高完成率的 universe 应该出现在 strength 列表中，且优先级更高
    assert strength_tags[0] == "universe"
    assert "self-care" in friction_tags


def test_recommendations_to_markdown_contains_suggested_mode_and_tags():
    insights = PlannerInsights(
        total_tasks=2,
        total_planned_events=5,
        total_completed_events=1,
        overall_completion_rate=0.2,
        tag_stats=[
            TagStats(tag="self-care", times_planned=3, times_completed=0),
            TagStats(tag="universe", times_planned=2, times_completed=1),
        ],
    )

    rec = build_self_model_recommendations(
        insights,
        min_planned_per_tag=1,
        top_n=2,
    )

    # overall 完成率很低，应建议 rest
    assert rec.suggested_base_mode == "rest"

    md = recommendations_to_markdown(rec)

    assert "Self Model Recommendations: Planner Strategy" in md
    assert "suggested base_mode" in md
    assert "rest" in md  # 推荐模式被渲染出来
    assert "`self-care`" in md
    assert "`universe`" in md

