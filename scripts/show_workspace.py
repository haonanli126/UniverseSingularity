from __future__ import annotations

"""
全局工作空间快照查看脚本（Workspace Snapshot v1）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/show_workspace.py

展示内容：
- 胚胎基础信息（来自 genome）
- 最近心境提示
- 最近对话（短期工作记忆）
- 长期记忆片段
- 最近一次自省
- 最近若干条「日记片段摘要」（来自 journal_entry 事件）
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
from src.us_core.core.workspace import build_workspace_state, DialogueMessage
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.journal import extract_journal_snippets_from_events


def _fmt_dt(dt):
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def main() -> None:
    settings = get_settings()
    genome = get_genome()

    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    long_term_path = PROJECT_ROOT / Path(genome.memory.long_term.archive_path)
    reflection_path = PROJECT_ROOT / Path(genome.metacognition.reflection_log_path)

    ws = build_workspace_state(
        session_log_path=session_log_path,
        long_term_path=long_term_path,
        reflection_path=reflection_path,
        max_recent_messages=8,
        max_long_term=5,
    )

    # 读取 session 事件中的 journal_entry
    session_events = []
    if session_log_path.exists():
        session_events = load_events_from_jsonl(session_log_path)
    journal_snippets = extract_journal_snippets_from_events(session_events, limit=3)

    print("=== Universe Singularity - Global Workspace Snapshot v1 ===")
    print(f"胚胎名称: {genome.embryo.name}")
    print(f"代号: {genome.embryo.codename}")
    print(f"Phase: {genome.embryo.phase}")
    print(f"环境: {settings.environment}")
    print()

    # 心境提示
    print("--- 心境提示 ---")
    if ws.mood_hint:
        print(ws.mood_hint)
    else:
        print("目前没有明显的心境提示。")
    print()

    # 最近对话
    print("--- 最近对话（短期工作记忆）---")
    if not ws.recent_dialogue:
        print("暂无最近对话记录。")
    else:
        for msg in ws.recent_dialogue:
            speaker = "你" if msg.role == "user" else "胚胎"
            print(f"{speaker}: {msg.text}")
    print()

    # 长期记忆
    print("--- 长期记忆（已归档的重要内容，最多 5 条）---")
    if not ws.long_term_memories:
        print("目前还没有长期记忆条目。")
    else:
        for idx, item in enumerate(ws.long_term_memories[:5], start=1):
            ts = _fmt_dt(item.timestamp)
            print(f"[{idx}] time: {ts}")
            print(f"    intent: {item.intent_label}")
            print(f"    text  : {item.text}")
    print()

    # 最近一次自省
    print("--- 最近一次自省 ---")
    if ws.last_reflection and ws.last_reflection_time:
        ts = _fmt_dt(ws.last_reflection_time)
        print(f"时间: {ts}")
        print("内容:")
        print(ws.last_reflection)
    else:
        print("目前还没有自省记录。")
    print()

    # 最近日记片段
    print("--- 日记片段（最近最多 3 条）---")
    if not journal_snippets:
        print("目前还没有导入的日记片段。")
        print("你可以在 data/journal/ 放入 .txt 文件，并运行 scripts/import_journal.py 导入。")
    else:
        for idx, snippet in enumerate(journal_snippets, start=1):
            print(f"[{idx}] {snippet}")
    print()


if __name__ == "__main__":
    main()
