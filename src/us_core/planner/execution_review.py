from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .loader import load_tasks_from_jsonl
from .models import Task


DONE_STATUSES = {"done", "completed", "cancelled", "canceled", "archived"}


@dataclass
class TaskExecution:
    """单个任务在本次计划中的执行情况。"""

    task_id: str
    title: Optional[str]
    status: Optional[str]
    is_completed: Optional[bool]


@dataclass
class ExecutionSummary:
    """整个计划的执行统计。"""

    total_planned: int
    found_tasks: int
    completed: int
    not_completed: int
    missing: int
    completion_rate: float
    items: List[TaskExecution]


def parse_task_ids_from_plan_markdown(markdown: str) -> List[str]:
    """从 Planner 生成的 Markdown 计划中解析任务 id 列表。

    兼容形如：
        - id: `abc123`
    或
        - id: abc123
    的行。
    """
    ids: List[str] = []
    for line in markdown.splitlines():
        s = line.strip()
        if not s.startswith("- id:"):
            continue

        # 优先从反引号中解析
        if "`" in s:
            parts = s.split("`")
            if len(parts) >= 2:
                task_id = parts[1].strip()
                if task_id:
                    ids.append(task_id)
                    continue

        # 退化方案：从冒号后截取
        _, _, tail = s.partition(":")
        tail = tail.strip()
        if tail:
            ids.append(tail)
    return ids


def load_execution_for_plan(
    task_ids: List[str],
    *,
    tasks_path: Optional[Path] = None,
) -> ExecutionSummary:
    """给定一份计划中涉及的 task_id 列表，对照 tasks.jsonl 计算执行情况。"""
    # 加载任务列表
    tasks = load_tasks_from_jsonl(tasks_path)
    id_to_task: Dict[str, Task] = {t.id: t for t in tasks}

    items: List[TaskExecution] = []
    found_tasks = 0
    completed = 0
    not_completed = 0
    missing = 0

    for tid in task_ids:
        task = id_to_task.get(tid)
        if task is None:
            items.append(
                TaskExecution(
                    task_id=tid,
                    title=None,
                    status=None,
                    is_completed=None,
                )
            )
            missing += 1
            continue

        found_tasks += 1
        status = task.status
        is_done = status.lower() in DONE_STATUSES if status else None
        if is_done:
            completed += 1
        else:
            not_completed += 1

        items.append(
            TaskExecution(
                task_id=tid,
                title=task.title,
                status=status,
                is_completed=is_done,
            )
        )

    total_planned = len(task_ids)
    completion_rate = (completed / found_tasks) if found_tasks > 0 else 0.0

    return ExecutionSummary(
        total_planned=total_planned,
        found_tasks=found_tasks,
        completed=completed,
        not_completed=not_completed,
        missing=missing,
        completion_rate=completion_rate,
        items=items,
    )


def execution_summary_to_markdown(
    summary: ExecutionSummary,
    *,
    plan_file: Optional[Path] = None,
) -> str:
    """把 ExecutionSummary 渲染为 Markdown 报告。"""
    lines: List[str] = []

    lines.append("# Plan Execution Review")
    lines.append("")
    if plan_file is not None:
        lines.append(f"- plan file: `{plan_file}`")
    lines.append(f"- total planned: **{summary.total_planned}**")
    lines.append(f"- tasks found in store: **{summary.found_tasks}**")
    lines.append(f"- completed: **{summary.completed}**")
    lines.append(f"- not completed: **{summary.not_completed}**")
    lines.append(f"- missing (not in tasks.jsonl): **{summary.missing}**")
    lines.append(f"- completion rate (found tasks): **{summary.completion_rate:.2%}**")
    lines.append("")

    if not summary.items:
        lines.append("> 本计划中没有任何任务。")
        return "\n".join(lines)

    lines.append("## Tasks")
    lines.append("")

    for idx, item in enumerate(summary.items, start=1):
        status_str: str
        if item.is_completed is True:
            status_str = "✅ completed"
        elif item.is_completed is False:
            status_str = "⬜ not completed"
        else:
            status_str = "❓ missing in tasks.jsonl"

        title = item.title or "(unknown title)"
        raw_status = item.status or "-"

        lines.append(f"### {idx}. {title}")
        lines.append("")
        lines.append(f"- id: `{item.task_id}`")
        lines.append(f"- status: `{raw_status}`")
        lines.append(f"- execution: {status_str}")
        lines.append("")

    return "\n".join(lines)


def analyze_plan_file(
    plan_path: Path,
    *,
    tasks_path: Optional[Path] = None,
) -> ExecutionSummary:
    """从一个 plan markdown 文件中解析任务并生成执行 summary。"""
    text = plan_path.read_text(encoding="utf-8")
    ids = parse_task_ids_from_plan_markdown(text)
    return load_execution_for_plan(ids, tasks_path=tasks_path)
