from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.self_model.insights import (  # type: ignore
    TagStats,
    PlannerInsights,
    compute_insights_from_enriched,
    insights_to_markdown,
)


def test_compute_insights_from_enriched_aggregates_correctly():
    enriched = [
        {
            "task_id": "1",
            "title": "T1",
            "tags": ["universe"],
            "times_planned": 3,
            "times_completed": 2,
            "completion_rate": 2 / 3,
        },
        {
            "task_id": "2",
            "title": "T2",
            "tags": ["self-care"],
            "times_planned": 2,
            "times_completed": 2,
            "completion_rate": 1.0,
        },
        {
            "task_id": "3",
            "title": "T3",
            "tags": ["universe", "self-care"],
            "times_planned": 1,
            "times_completed": 0,
            "completion_rate": 0.0,
        },
    ]

    insights = compute_insights_from_enriched(enriched)

    assert insights.total_tasks == 3
    assert insights.total_planned_events == 6
    assert insights.total_completed_events == 4
    assert insights.overall_completion_rate == 4 / 6

    by_tag = {ts.tag: ts for ts in insights.tag_stats}
    # universe: 3 + 1 次规划, 完成 2 + 0
    assert by_tag["universe"].times_planned == 4
    assert by_tag["universe"].times_completed == 2
    assert abs(by_tag["universe"].completion_rate - 0.5) < 1e-6

    # self-care: 2 + 1 次规划, 完成 2 + 0
    assert by_tag["self-care"].times_planned == 3
    assert by_tag["self-care"].times_completed == 2
    assert abs(by_tag["self-care"].completion_rate - (2 / 3)) < 1e-6


def test_insights_to_markdown_contains_best_and_worst_tags():
    enriched = [
        {
            "task_id": "1",
            "title": "T1",
            "tags": ["universe"],
            "times_planned": 3,
            "times_completed": 1,
            "completion_rate": 1 / 3,
        },
        {
            "task_id": "2",
            "title": "T2",
            "tags": ["self-care"],
            "times_planned": 3,
            "times_completed": 3,
            "completion_rate": 1.0,
        },
    ]

    insights = compute_insights_from_enriched(enriched)
    md = insights_to_markdown(insights, top_n=2, min_planned_per_tag=1)

    # 顶部信息
    assert "Self Model Snapshot: Planner Habits" in md
    assert "overall completion rate" in md

    # 分标签信息
    assert "Tags with highest completion rate" in md
    assert "`self-care`" in md
    assert "Tags with lowest completion rate" in md
    assert "`universe`" in md
