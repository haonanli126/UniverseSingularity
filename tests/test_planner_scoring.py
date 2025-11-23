from pathlib import Path
import sys
from datetime import datetime, timedelta

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.models import Task
from us_core.planner.scoring import score_task


def test_rest_mode_prefers_self_care_over_universe():
    now = datetime.now()
    t_self = Task(id="1", title="stretch", tags=["self-care"], created_at=now)
    t_universe = Task(id="2", title="build UniverseSingularity", tags=["universe"], created_at=now)

    score_self, _ = score_task(t_self, mode="rest", now=now)
    score_universe, _ = score_task(t_universe, mode="rest", now=now)

    assert score_self > score_universe


def test_focus_mode_prefers_universe_over_self_care():
    now = datetime.now()
    t_self = Task(id="1", title="stretch", tags=["self-care"], created_at=now)
    t_universe = Task(id="2", title="build UniverseSingularity", tags=["universe"], created_at=now)

    score_self, _ = score_task(t_self, mode="focus", now=now)
    score_universe, _ = score_task(t_universe, mode="focus", now=now)

    assert score_universe > score_self


def test_priority_increases_score_in_focus_mode():
    now = datetime.now()
    low = Task(id="1", title="low", priority=1, created_at=now)
    high = Task(id="2", title="high", priority=3, created_at=now)

    low_score, _ = score_task(low, mode="focus", now=now)
    high_score, _ = score_task(high, mode="focus", now=now)

    assert high_score > low_score


def test_recency_component_makes_newer_task_better():
    now = datetime.now()
    old = Task(id="1", title="old", created_at=now - timedelta(days=20))
    new = Task(id="2", title="new", created_at=now - timedelta(days=1))

    old_score, _ = score_task(old, mode="balance", now=now)
    new_score, _ = score_task(new, mode="balance", now=now)

    assert new_score > old_score
