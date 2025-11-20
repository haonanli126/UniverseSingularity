from __future__ import annotations

"""
查看对话日志中的意图分布：

(.venv) PS D:/UniverseSingularity> python scripts/show_intents.py
"""

import sys
from collections import Counter
from pathlib import Path

from typing import Dict

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.genome import get_genome
from src.us_core.core.events import EmbryoEvent
from src.us_core.core.persistence import load_events_from_jsonl


def main() -> None:
    genome = get_genome()
    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)

    print("=== Universe Singularity - Intent Overview v0 ===")
    print(f"会话日志路径: {session_log_path}")
    print()

    if not session_log_path.exists():
        print("会话日志不存在。先和胚胎聊几句吧。")
        return

    events = load_events_from_jsonl(session_log_path)
    intents: Counter[str] = Counter()

    for e in events:
        payload = e.payload or {}
        intent: Dict | None = payload.get("intent")
        if not intent:
            continue
        label = str(intent.get("label") or "unknown")
        intents[label] += 1

    if not intents:
        print("目前还没有带 intent 的事件（可能是之前老版本生成的日志）。")
        return

    total = sum(intents.values())
    print(f"共统计到 {total} 条带 intent 的用户事件：\n")
    for label, count in intents.most_common():
        pct = count * 100.0 / total
        print(f"- {label}: {count} 条（约 {pct:.1f}%）")


if __name__ == "__main__":
    main()
