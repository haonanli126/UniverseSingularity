from __future__ import annotations

"""
长期记忆收集脚本（Long-term Memory Collector v0）：

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/collect_long_term.py

- 从 session_log.jsonl 读取所有会话事件
- 从 long_term.jsonl 读取已有长期记忆事件
- 通过规则筛选应当进入长期记忆的用户发言
- 去重后将新增的 MEMORY 事件写入 long_term.jsonl
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
from src.us_core.core.long_term import prepare_long_term_events
from src.us_core.core.persistence import (
    load_events_from_jsonl,
    append_event_to_jsonl,
)


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("collect_long_term")

    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    archive_log_path = PROJECT_ROOT / Path(genome.memory.long_term.archive_path)

    print("=== Universe Singularity - Long-term Memory Collector v0 ===")
    print(f"当前环境: {settings.environment}")
    print(f"会话日志路径: {session_log_path}")
    print(f"长期记忆路径: {archive_log_path}")
    print()

    if not session_log_path.exists():
        print("会话日志不存在，先和胚胎聊一聊再来吧。")
        return

    all_events = load_events_from_jsonl(session_log_path)
    existing_archive = load_events_from_jsonl(archive_log_path)

    print(f"读取到会话事件总数: {len(all_events)}")
    print(f"当前长期记忆事件数: {len(existing_archive)}")

    new_archive_events = prepare_long_term_events(all_events, existing_archive)

    if not new_archive_events:
        print("本轮没有新的内容需要归档到长期记忆。")
        return

    for e in new_archive_events:
        append_event_to_jsonl(archive_log_path, e)

    print(f"本轮新增长期记忆事件数: {len(new_archive_events)}")
    logger.info(
        "Long-term memory collected %d new events.", len(new_archive_events)
    )


if __name__ == "__main__":
    main()
