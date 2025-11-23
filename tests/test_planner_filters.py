from pathlib import Path
import sys

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.filters import filter_tasks
from us_core.planner.models import FilterSpec, Task


def _make_task(id_: str, title: str, status: str = "open", priority: int | None = None, tags=None):
    return Task(
        id=id_,
        title=title,
        status=status,
        priority=priority,
        tags=tags or [],
    )


def test_filter_by_status_and_priority():
    tasks = [
        _make_task("1", "open low", status="open", priority=1),
        _make_task("2", "open high", status="open", priority=3),
        _make_task("3", "done high", status="done", priority=3),
    ]

    spec = FilterSpec(statuses={"open"}, min_priority=2)
    result = filter_tasks(tasks, spec)

    ids = {t.id for t in result}
    assert ids == {"2"}


def test_filter_include_and_exclude_tags():
    tasks = [
        _make_task("1", "self care", tags=["self-care", "life"]),
        _make_task("2", "universe deep", tags=["universe", "deep-work"]),
        _make_task("3", "mixed", tags=["self-care", "universe"]),
        _make_task("4", "other", tags=["misc"]),
    ]

    spec = FilterSpec(include_tags={"self-care"}, exclude_tags={"universe"})
    result = filter_tasks(tasks, spec)

    ids = {t.id for t in result}
    # 只剩下纯 self-care 的任务
    assert ids == {"1"}


def test_filter_by_search_keyword():
    tasks = [
        _make_task("1", "buy groceries", tags=["life"]),
        _make_task("2", "design UniverseSingularity planner", tags=["universe"]),
        _make_task("3", "sleep", tags=["self-care"]),
    ]

    spec = FilterSpec(search="universe")
    result = filter_tasks(tasks, spec)

    ids = {t.id for t in result}
    assert ids == {"2"}
