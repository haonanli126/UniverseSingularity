from pathlib import Path
import sys

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.daily_review import (  # type: ignore
    NamedExecutionSummary,
    aggregate_execution_summaries,
    daily_review_to_markdown,
)
from us_core.planner.execution_review import ExecutionSummary, TaskExecution  # type: ignore


def _make_summary(
    planned: int,
    found: int,
    completed: int,
    not_completed: int,
    missing: int,
) -> ExecutionSummary:
    # 这里 items 不重要，只要给个空列表即可
    completion_rate = completed / found if found > 0 else 0.0
    return ExecutionSummary(
        total_planned=planned,
        found_tasks=found,
        completed=completed,
        not_completed=not_completed,
        missing=missing,
        completion_rate=completion_rate,
        items=[],
    )


def test_aggregate_execution_summaries_sums_correctly():
    s1 = _make_summary(planned=3, found=2, completed=1, not_completed=1, missing=1)
    s2 = _make_summary(planned=2, found=2, completed=2, not_completed=0, missing=0)

    named = [
        NamedExecutionSummary(plan_name="p1", summary=s1),
        NamedExecutionSummary(plan_name="p2", summary=s2),
    ]

    agg = aggregate_execution_summaries(named)

    assert agg.total_plans == 2
    assert agg.total_planned == 5
    assert agg.total_found == 4
    assert agg.total_completed == 3
    assert agg.total_not_completed == 1
    assert agg.total_missing == 1
    assert agg.overall_completion_rate == 3 / 4


def test_daily_review_to_markdown_contains_overall_and_per_plan_info():
    s1 = _make_summary(planned=3, found=2, completed=1, not_completed=1, missing=1)
    named = [NamedExecutionSummary(plan_name="plan.md", summary=s1)]

    agg = aggregate_execution_summaries(named)
    md = daily_review_to_markdown(agg)

    assert "Daily Plan Execution Review" in md
    assert "total plans" in md
    assert "plan.md" in md
    assert "completion rate" in md
