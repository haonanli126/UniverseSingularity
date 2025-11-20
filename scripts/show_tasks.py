from __future__ import annotations

"""
任务板查看器（Task Board Viewer v0）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/show_tasks.py

- 读取 data/tasks/tasks.jsonl
- 展示当前未完成的任务列表
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.tasks import get_open_tasks


def _fmt_dt(dt):
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def main() -> None:
    tasks_path = PROJECT_ROOT / Path("data/tasks/tasks.jsonl")

    print("=== Universe Singularity - Task Board v0 ===")
    print(f"任务列表路径: {tasks_path}")
    print()

    if not tasks_path.exists():
        print("任务文件不存在。可以先运行 python scripts/collect_tasks.py 来从对话中收集任务。")
        return

    all_task_events = load_events_from_jsonl(tasks_path)
    if not all_task_events:
        print("任务文件存在，但目前还没有任务。")
        return

    open_tasks = get_open_tasks(all_task_events)

    print(f"当前任务总数: {len(all_task_events)}")
    print(f"其中未完成任务数: {len(open_tasks)}")
    print()

    if not open_tasks:
        print("目前没有未完成的任务，任务板是空的。")
        return

    for idx, e in enumerate(open_tasks, start=1):
        payload = e.payload or {}
        text = str(payload.get("text") or "")
        intent = payload.get("intent") or {}
        label = str(intent.get("label") or "command")
        status = str(payload.get("status") or "open")
        ts = _fmt_dt(e.timestamp)

        print(f"[{idx}] time: {ts}")
        print(f"    status: {status}")
        print(f"    intent: {label}")
        print(f"    text  : {text}")
        print()


if __name__ == "__main__":
    main()
