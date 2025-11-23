from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.models import Task  # type: ignore
from us_core.planner.scoring import score_task, score_task_with_history  # type: ignore
from us_core.planner.preference_memory import TaskHistoryStats  # type: ignore


def test_score_task_with_history_prefers_higher_completion_rate():
    now = datetime(2025, 1, 1, 12, 0, 0)

    t1 = Task(id="1", title="Task 1", status="open", priority=1, tags=[], created_at=now)
    t2 = Task(id="2", title="Task 2", status="open", priority=1, tags=[], created_at=now)

    # 基础打分应该相同
    base1, _ = score_task(t1, mode="focus", now=now)
    base2, _ = score_task(t2, mode="focus", now=now)
    assert base1 == base2

    # 历史完成率不同
    stats = {
        "1": TaskHistoryStats(task_id="1", times_planned=5, times_completed=1),  # 20%
        "2": TaskHistoryStats(task_id="2", times_planned=5, times_completed=4),  # 80%
    }

    s1, comp1 = score_task_with_history(t1, mode="focus", history_stats=stats, now=now)
    s2, comp2 = score_task_with_history(t2, mode="focus", history_stats=stats, now=now)

    # 高完成率任务应该更受偏好加成
    assert s2 > s1
    assert "preference" in comp1
    assert "preference" in comp2
