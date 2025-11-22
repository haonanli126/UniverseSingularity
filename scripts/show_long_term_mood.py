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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 长期情绪曲线视图 (Phase 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）查看最近 7 天的长期情绪：
                  python .\\scripts\\show_long_term_mood.py --days 7

              2）查看最近 14 天：
                  python .\\scripts\\show_long_term_mood.py --days 14

              3）自定义文件路径（例如其它长期记忆导出文件）：
                  python .\\scripts\\show_long_term_mood.py --file path/to/xxx.jsonl
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
        help="最多展示多少天的记录（按日期从旧到新），默认 7。",
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

    # 只展示最近 N 天
    days_to_show = max(1, args.days)
    if len(daily) > days_to_show:
        daily = daily[-days_to_show:]

    first_day = daily[0].day.isoformat()
    last_day = daily[-1].day.isoformat()
    print(
        f"长期情绪视图：{first_day} ~ {last_day}（共 {len(daily)} 天）\n"
        f"说明：average_score 越接近 1 越偏正面，越接近 -1 越偏负面。\n"
    )

    for d in daily:
        day_str = d.day.isoformat()
        print(
            f"{day_str} | {d.label} | "
            f"平均情绪 {d.average_score:+.2f} | 样本数 {d.sample_count}"
        )


if __name__ == "__main__":
    main()
