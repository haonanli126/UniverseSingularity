from __future__ import annotations

"""
情绪雷达面板（Mood Overview v0）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/show_mood.py

展示内容：
- 从长期记忆（intent=emotion）和日记（journal_entry）提取情绪样本
- 计算按天聚合的情绪平均值和大致标签
- 列出最近若干条情绪样本（含来源与简短文本）
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
from src.us_core.core.workspace import build_workspace_state
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.mood import (
    build_mood_samples_from_long_term,
    build_mood_samples_from_journal_events,
    aggregate_daily_mood,
)


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("show_mood")

    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    long_term_path = PROJECT_ROOT / Path(genome.memory.long_term.archive_path)

    print("=== Universe Singularity - Mood Overview v0 ===")
    print(f"环境: {settings.environment}")
    print(f"会话日志: {session_log_path}")
    print(f"长期记忆: {long_term_path}")
    print()

    # 1) 从 Workspace 里拿长期记忆（含 emotion 标签）
    ws = build_workspace_state(
        session_log_path=session_log_path,
        long_term_path=long_term_path,
        reflection_path=PROJECT_ROOT / Path(genome.metacognition.reflection_log_path),
        max_recent_messages=8,
        max_long_term=100,
    )
    lt_samples = build_mood_samples_from_long_term(ws.long_term_memories)

    # 2) 从 session_log 中提取日记类情绪样本
    journal_events = []
    if session_log_path.exists():
        journal_events = load_events_from_jsonl(session_log_path)
    journal_samples = build_mood_samples_from_journal_events(journal_events)

    all_samples = lt_samples + journal_samples
    all_samples.sort(key=lambda s: s.timestamp)

    if not all_samples:
        print("目前还没有可以用于分析的情绪样本。")
        print("你可以：")
        print("1）多和我聊聊你的感受（会进入长期记忆）；")
        print("2）在 data/journal/ 写一点心情日记并导入。")
        return

    # 3) 按天聚合
    daily = aggregate_daily_mood(all_samples)

    print("--- 每日情绪概览 ---")
    for d in daily:
        # 简单的「条形图」：根据平均分长度显示 +- 号
        bar_len = int(abs(d.average_score) * 4)  # 最多 8 个字符
        if d.average_score > 0:
            bar = "+" * bar_len
        elif d.average_score < 0:
            bar = "-" * bar_len
        else:
            bar = ""
        print(
            f"{d.day.isoformat()}  "
            f"avg={d.average_score:.2f}  "
            f"({d.label})  "
            f"{bar}"
        )
    print()

    # 4) 列出最近几条原始情绪样本
    print("--- 最近情绪样本（最多 5 条）---")
    for s in all_samples[-5:]:
        ts_str = s.timestamp.astimezone().strftime("%Y-%m-%d %H:%M")
        print(f"[{ts_str}] [{s.source}] score={s.score} ({s.label})")
        print(f"  {s.text}")
    print()

    logger.info(
        "Displayed mood overview: %d daily buckets, %d samples",
        len(daily),
        len(all_samples),
    )


if __name__ == "__main__":
    main()
