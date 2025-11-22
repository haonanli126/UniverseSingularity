from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from export_today_plan_with_mood import export_today_plan_markdown


def test_export_today_plan_markdown_basic(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    memory_path = tmp_path / "perception_long_term.jsonl"
    output_path = tmp_path / "today_plan.md"

    # 构造 3 条任务：2 个 open，1 个 done
    tasks = [
        {"id": "1", "title": "open-task-a", "priority": 5, "status": "open"},
        {"id": "2", "title": "open-task-b", "priority": 1, "status": "open"},
        {"id": "3", "title": "done-task-c", "priority": 3, "status": "done"},
    ]
    with tasks_path.open("w", encoding="utf-8") as f:
        for t in tasks:
            json.dump(t, f, ensure_ascii=False)
            f.write("\n")

    # 构造简单的长期情绪文件（同一天两条情绪）
    now = datetime(2025, 1, 2, 12, 0, tzinfo=timezone.utc)
    events = [
        {
            "text": "今天很开心",
            "intent_label": "emotion",
            "timestamp": now.isoformat(),
        },
        {
            "text": "有点累",
            "intent_label": "emotion",
            "timestamp": now.isoformat(),
        },
    ]
    with memory_path.open("w", encoding="utf-8") as f:
        for e in events:
            json.dump(e, f, ensure_ascii=False)
            f.write("\n")

    export_today_plan_markdown(
        tasks_path=tasks_path,
        memory_path=memory_path,
        days=7,
        output_path=output_path,
    )

    content = output_path.read_text(encoding="utf-8")

    # 基本结构检查
    assert "今日计划（情绪感知版）" in content
    assert "情绪概况" in content
    assert "自我照顾模式" in content

    # 任务信息检查：open / done 都应该出现在文档中
    assert "open-task-a" in content
    assert "open-task-b" in content
    assert "done-task-c" in content

    # 勾选框格式：未完成用 [ ]，已完成用 [x]
    assert "- [ ]" in content
    assert "- [x]" in content
