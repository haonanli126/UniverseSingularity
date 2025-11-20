from __future__ import annotations

"""
任务完成标记脚本（Complete Task v0）：

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/complete_task.py

- 读取 data/tasks/tasks.jsonl
- 展示当前未完成任务
- 让你选择一个编号，将其标记为 done
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from src.us_core.utils.logger import setup_logger
from src.us_core.core.persistence import load_events_from_jsonl, append_event_to_jsonl
from src.us_core.core.tasks import get_open_tasks, set_task_status


def _fmt_dt(dt):
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def main() -> None:
    settings = get_settings()
    logger = setup_logger("complete_task")

    tasks_path = PROJECT_ROOT / Path("data/tasks/tasks.jsonl")

    print("=== Universe Singularity - Complete Task v0 ===")
    print(f"环境: {settings.environment}")
    print(f"任务文件路径: {tasks_path}")
    print()

    if not tasks_path.exists():
        print("任务文件不存在。可以先运行 python scripts/collect_tasks.py 从对话中收集任务。")
        return

    all_events = load_events_from_jsonl(tasks_path)
    open_tasks = get_open_tasks(all_events)

    if not open_tasks:
        print("目前没有未完成的任务，任务板是空的。")
        return

    print(f"当前未完成任务数: {len(open_tasks)}")
    print("下面是当前的 open 任务：\n")

    for idx, e in enumerate(open_tasks, start=1):
        payload = e.payload or {}
        text = str(payload.get("text") or "")
        ts = _fmt_dt(e.timestamp)
        status = str(payload.get("status") or "open")
        print(f"[{idx}] time  : {ts}")
        print(f"    status: {status}")
        print(f"    text  : {text}")
        print()

    # 让用户选择一个任务编号
    while True:
        choice = input("请输入要标记完成的任务编号（或输入 q 退出）：").strip()
        if not choice:
            continue

        if choice.lower() in {"q", "quit", "exit"}:
            print("已取消，本次不修改任何任务状态。")
            return

        try:
            idx = int(choice)
        except ValueError:
            print("请输入有效的数字编号，或 q 退出。")
            continue

        if idx < 1 or idx > len(open_tasks):
            print(f"请输入 1 到 {len(open_tasks)} 之间的编号。")
            continue

        target_event = open_tasks[idx - 1]
        break

    # 在内存中更新状态
    set_task_status(all_events, [target_event.id], "done")

    # 重写任务文件：先删除原文件，再逐条 append 回去
    tasks_path.unlink()
    for e in all_events:
        append_event_to_jsonl(tasks_path, e)

    print()
    print("已将选定任务标记为 done。")
    logger.info("Marked task %s as done.", target_event.id)


if __name__ == "__main__":
    main()
