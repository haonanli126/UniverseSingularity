from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

# --- 确保可以从项目根目录 / src 导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception.long_term_view import build_daily_mood_from_memory_file
from us_core.core.mood_summary import (
    summarize_weekly_mood,
    generate_weekly_mood_summary_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 一周情绪小结 (Phase 2-S04)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）查看最近 7 天的一周情绪小结：
                  python .\\scripts\\weekly_mood_summary.py --days 7

              2）查看最近 14 天：
                  python .\\scripts\\weekly_mood_summary.py --days 14

              3）指定其它长期记忆文件：
                  python .\\scripts\\weekly_mood_summary.py --file path/to/xxx.jsonl --days 7
            """
        ),
    )

    parser.add_argument(
        "--file",
        type=str,
        default="",
        help="长期情绪 JSONL 文件路径，默认使用 data/memory/perception_long_term.jsonl。",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="最多纳入多少天的记录（按日期从旧到新取最后 N 天），默认 7。",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file:
        path = Path(args.file)
    else:
        path = PROJECT_ROOT / "data" / "memory" / "perception_long_term.jsonl"

    daily = build_daily_mood_from_memory_file(path)

    if not daily:
        print(f"在 {path} 中暂时没有可用的长期情绪记录。")
        print("可以先用 perception_cli / dialog_cli 说说最近的状态，然后再用 ingest_perception_to_memory 写入长期记忆。")
        return

    # 截取最近 N 天
    days_to_use = max(1, args.days)
    if len(daily) > days_to_use:
        daily = daily[-days_to_use:]

    summary = summarize_weekly_mood(daily)
    text = generate_weekly_mood_summary_text(summary)

    print("==============================================")
    print(" Universe Singularity · 一周情绪小结 (Phase 2)")
    print("==============================================\n")
    print(text)


if __name__ == "__main__":
    main()
