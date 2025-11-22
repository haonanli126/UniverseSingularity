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
from us_core.core.self_care import build_self_care_suggestion


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 今日自我照顾建议 (Phase 3-S01)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）基于最近 7 天的长期情绪记录给出今日自我照顾建议：
                  python .\\scripts\\self_care_today.py --days 7

              2）基于最近 3 天（更敏感）：
                  python .\\scripts\\self_care_today.py --days 3

              3）指定其他长期情绪文件：
                  python .\\scripts\\self_care_today.py --file path/to/xxx.jsonl --days 7
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
        help="纳入考虑的最大天数（从最近往前数，默认 7 天）。",
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

    days_to_use = max(1, args.days)
    if len(daily) > days_to_use:
        daily = daily[-days_to_use:]

    suggestion = build_self_care_suggestion(daily)
    if suggestion is None:
        print("目前还没有足够的情绪数据来给出建议，有空可以多和我聊聊。")
        return

    first_day = daily[0].day.isoformat()
    last_day = daily[-1].day.isoformat()

    print("==============================================")
    print(" Universe Singularity · 今日自我照顾建议")
    print("==============================================\n")
    print(f"参考时间范围：{first_day} ~ {last_day}（共 {len(daily)} 天）")
    print(f"最近几天的平均情绪分：{suggestion.average_mood:+.2f}")
    print(f"建议模式：{suggestion.mode}\n")
    print(suggestion.message)


if __name__ == "__main__":
    main()
