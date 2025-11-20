from __future__ import annotations

"""
测试 TODO 导出器（export_todo.py）

目标：
- 当存在 open / done 两种任务时，只导出 open 任务
- 使用规划日志中「最新一条」规划
- 导出的 markdown 文件中包含任务文本与规划内容
"""

from datetime import datetime, timezone
from pathlib import Path

from scripts import export_todo as m
from src.us_core.core.events import EmbryoEvent, EventType


def test_export_todo_uses_open_tasks_and_latest_plan(tmp_path, monkeypatch):
    # 让 export_todo 在临时目录下工作，而不是真实项目目录
    monkeypatch.setattr(m, "PROJECT_ROOT", tmp_path)

    tasks_path = tmp_path / "data/tasks/tasks.jsonl"
    plans_path = tmp_path / "data/plans/plans.jsonl"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    plans_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.touch()
    plans_path.touch()

    now = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

    # 构造两个任务事件：一个 open，一个 done
    # 注意：项目里任务事件实际使用的是 EventType.MEMORY，
    # 通过 payload.status / payload.text 等字段区分。
    open_task = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={
            "status": "open",
            "intent": "command",
            "text": "测试开放任务：整理 Universe Singularity 规划。",
        },
    )
    done_task = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={
            "status": "done",
            "intent": "command",
            "text": "已完成的任务不应出现在 TODO 中。",
        },
    )

    # 构造两条规划事件：后一条时间更晚，应该被视为最新规划
    # 这里同样用 EventType.MEMORY，和真实 planning_session 写入方式保持一致
    plan_event_old = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={
            "summary": "旧规划，不应该作为最新使用。",
            "full_text": "旧规划内容。",
        },
    )
    plan_event_new = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now.replace(hour=13),
        payload={
            "summary": "测试规划概要",
            "full_text": "详细规划内容行1\n详细规划内容行2",
        },
    )

    fake_tasks_events = [open_task, done_task]
    fake_plans_events = [plan_event_old, plan_event_new]

    def fake_loader(path: Path):
        if path == tasks_path:
            return fake_tasks_events
        if path == plans_path:
            return fake_plans_events
        return []

    # 把 export_todo 内部用到的 load_events_from_jsonl 替换为我们的假实现
    monkeypatch.setattr(m, "load_events_from_jsonl", fake_loader)

    # 运行导出逻辑
    m.main()

    todo_path = tmp_path / "data/todo/todo.md"
    assert todo_path.exists()

    content = todo_path.read_text(encoding="utf-8")

    # 1) open 任务应该出现在 TODO 中
    assert "测试开放任务：整理 Universe Singularity 规划。" in content
    # 2) done 任务不应该出现在 TODO 中
    assert "已完成的任务不应出现在 TODO 中" not in content

    # 3) 只使用最新规划（测试规划概要 + 详细内容）
    assert "测试规划概要" in content
    assert "详细规划内容行1" in content
    assert "旧规划内容" not in content
