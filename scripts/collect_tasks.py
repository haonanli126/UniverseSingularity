from __future__ import annotations

"""
任务收集器（Task Collector v0）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/collect_tasks.py

- 从会话日志 session_log.jsonl 中扫描用户的 command 意图发言
- 生成任务事件（MEMORY, kind="task"）
- 写入 data/tasks/tasks.jsonl
- 支持基于 original_event_id 去重
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.utils.logger import setup_logger
from src.us_core.core.tasks import prepare_task_events
from src.us_core.core.persistence import (
    load_events_from_jsonl,
    append_event_to_jsonl,
)


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("collect_tasks")

    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    tasks_path = PROJECT_ROOT / Path("data/tasks/tasks.jsonl")

    print("=== Universe Singularity - Task Collector v0 ===")
    print(f"当前环境: {settings.environment}")
    print(f"会话日志路径: {session_log_path}")
    print(f"任务列表路径: {tasks_path}")
    print()

    if not session_log_path.exists():
        print("会话日志不存在，先和胚胎聊一聊、给它一些指令再来捞任务。")
        return

    all_events = load_events_from_jsonl(session_log_path)
    if tasks_path.exists():
        existing_tasks = load_events_from_jsonl(tasks_path)
    else:
        existing_tasks = []

    print(f"读取到会话事件总数: {len(all_events)}")
    print(f"当前任务事件数: {len(existing_tasks)}")

    new_task_events = prepare_task_events(all_events, existing_tasks)

    if not new_task_events:
        print("本轮没有新的任务需要加入任务板。")
        return

    for e in new_task_events:
        append_event_to_jsonl(tasks_path, e)

    print(f"本轮新增任务数: {len(new_task_events)}")
    logger.info("Task collector added %d new tasks.", len(new_task_events))


if __name__ == "__main__":
    main()
