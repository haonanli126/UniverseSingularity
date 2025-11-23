from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .execution_review import ExecutionSummary
from .loader import load_tasks_from_jsonl
from .models import Task


@dataclass
class TaskHistoryStats:
    """某个任务在历史上的规划 / 完成统计。"""

    task_id: str
    times_planned: int = 0
    times_completed: int = 0

    @property
    def completion_rate(self) -> float:
        if self.times_planned == 0:
            return 0.0
        return self.times_completed / self.times_planned


def _project_root_from_this_file() -> Path:
    # src/us_core/planner/preference_memory.py
    return Path(__file__).resolve().parents[3]


def get_history_path() -> Path:
    project_root = _project_root_from_this_file()
    return project_root / "data" / "plans" / "planner_history.jsonl"


def append_execution_summary(
    plan_name: str,
    summary: ExecutionSummary,
    *,
    history_path: Optional[Path] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """把一次 ExecutionSummary 追加写入 planner_history.jsonl。

    结构包含：
    - 每个 task 的执行记录：type = "task_execution"
    - 这次 plan 的整体 summary：type = "plan_summary"
    """
    if history_path is None:
        history_path = get_history_path()
    history_path.parent.mkdir(parents=True, exist_ok=True)

    if timestamp is None:
        timestamp = datetime.now()

    ts = timestamp.isoformat()

    with history_path.open("a", encoding="utf-8") as f:
        # 任务级别事件
        for item in summary.items:
            rec = {
                "type": "task_execution",
                "timestamp": ts,
                "plan_name": plan_name,
                "task_id": item.task_id,
                "title": item.title,
                "status": item.status,
                "is_completed": item.is_completed,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # 整体计划 summary
        rec_summary = {
            "type": "plan_summary",
            "timestamp": ts,
            "plan_name": plan_name,
            "total_planned": summary.total_planned,
            "found_tasks": summary.found_tasks,
            "completed": summary.completed,
            "not_completed": summary.not_completed,
            "missing": summary.missing,
            "completion_rate": summary.completion_rate,
        }
        f.write(json.dumps(rec_summary, ensure_ascii=False) + "\n")


def load_history(history_path: Optional[Path] = None) -> List[dict]:
    """加载 planner_history.jsonl 中所有记录。"""
    if history_path is None:
        history_path = get_history_path()

    if not history_path.exists():
        return []

    records: List[dict] = []
    with history_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            records.append(rec)
    return records


def aggregate_task_stats_from_records(records: Iterable[dict]) -> Dict[str, TaskHistoryStats]:
    """从 history 记录中聚合出每个 task_id 的统计。"""
    stats: Dict[str, TaskHistoryStats] = {}

    for rec in records:
        if rec.get("type") != "task_execution":
            continue

        task_id_raw = rec.get("task_id")
        if task_id_raw is None:
            continue
        task_id = str(task_id_raw)

        entry = stats.get(task_id)
        if entry is None:
            entry = TaskHistoryStats(task_id=task_id)
            stats[task_id] = entry

        entry.times_planned += 1
        if rec.get("is_completed") is True:
            entry.times_completed += 1

    return stats


def aggregate_task_stats(history_path: Optional[Path] = None) -> Dict[str, TaskHistoryStats]:
    """便捷方法：直接从 history 文件聚合任务统计。"""
    records = load_history(history_path)
    return aggregate_task_stats_from_records(records)


def attach_task_metadata(
    stats: Dict[str, TaskHistoryStats],
    *,
    tasks_path: Optional[Path] = None,
) -> List[dict]:
    """把当前 tasks.jsonl 中的任务信息 join 进统计结果里，方便展示。"""
    tasks = load_tasks_from_jsonl(tasks_path)
    id_to_task: Dict[str, Task] = {t.id: t for t in tasks}

    enriched: List[dict] = []
    for task_id, st in stats.items():
        task = id_to_task.get(task_id)
        title = task.title if task is not None else None
        tags = task.tags if task is not None else []

        enriched.append(
            {
                "task_id": task_id,
                "title": title,
                "tags": tags,
                "times_planned": st.times_planned,
                "times_completed": st.times_completed,
                "completion_rate": st.completion_rate,
            }
        )

    return enriched
