from __future__ import annotations

"""
长期记忆浏览器（Long-term Memory Viewer v0）：

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/show_long_term.py

- 从 genome.memory.long_term.archive_path 读取长期记忆文件
- 展示最近若干条长期记忆（倒序）
"""

import sys
from pathlib import Path
from typing import Dict

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.genome import get_genome
from src.us_core.core.long_term import get_recent_archive_events
from src.us_core.core.persistence import load_events_from_jsonl


def _shorten(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _extract_intent(payload: Dict) -> str:
    intent = payload.get("intent") or {}
    label = intent.get("label") or "unknown"
    return str(label)


def main() -> None:
    genome = get_genome()

    archive_rel = Path(genome.memory.long_term.archive_path)
    archive_path = PROJECT_ROOT / archive_rel

    print("=== Universe Singularity - Long-term Memory Viewer v0 ===")
    print(f"长期记忆路径: {archive_path}")
    print()

    if not archive_path.exists():
        print("长期记忆文件不存在。先运行 python scripts/collect_long_term.py 生成一些记忆吧。")
        return

    events = load_events_from_jsonl(archive_path)
    if not events:
        print("长期记忆文件存在，但目前为空。")
        return

    recent = get_recent_archive_events(events, limit=10)

    print(f"当前长期记忆总条数: {len(events)}")
    print(f"下面展示最近 {len(recent)} 条（按时间倒序）：")
    print()

    for idx, e in enumerate(recent, start=1):
        payload = e.payload or {}
        text = str(payload.get("text") or "")
        intent_label = _extract_intent(payload)
        ts = e.timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

        print(f"[{idx}] time: {ts}")
        print(f"    intent: {intent_label}")
        print(f"    text  : {_shorten(text)}")
        print()

    print("（你可以以后基于这些长期记忆，再做更高级的检索 / 总结／RAG。）")


if __name__ == "__main__":
    main()
