from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from textwrap import dedent

# --- 确保可以从项目根目录 / src 导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import PerceptionStore
from us_core.perception.memory_bridge import ingest_perception_events_to_file
from us_core.perception.long_term_view import build_daily_mood_from_memory_file
from us_core.core.mood_summary import generate_weekly_mood_summary_text
from us_core.core.daily_reflection import build_daily_reflection_context


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 日终小结 (Phase 3-S02)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）使用默认配置做一次完整日终小结（最近 7 天）：
                  python .\\scripts\\daily_reflection.py

              2）控制纳入的天数，例如只看最近 3 天：
                  python .\\scripts\\daily_reflection.py --days 3

              3）调整本次从感知写入长期记忆的最大条数：
                  python .\\scripts\\daily_reflection.py --ingest-limit 100

              4）指定自定义的长期情绪 JSONL 文件：
                  python .\\scripts\\daily_reflection.py --file path/to/xxx.jsonl
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
        help="纳入小结的最大天数（从最近往前数，默认 7 天）。",
    )
    parser.add_argument(
        "--ingest-limit",
        type=int,
        default=200,
        help="本次从感知事件中最多写入多少条长期情绪记忆（默认 200）。",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1）确定长期情绪文件路径
    if args.file:
        memory_path = Path(args.file)
    else:
        memory_path = PROJECT_ROOT / "data" / "memory" / "perception_long_term.jsonl"

    # 2）从感知仓库写入最新的长期情绪记忆
    store = PerceptionStore()
    limit = args.ingest_limit if args.ingest_limit and args.ingest_limit > 0 else None

    written_items = ingest_perception_events_to_file(
        store,
        output_path=memory_path,
        channel=None,
        limit=limit,
    )

    # 3）根据长期情绪文件构建每日情绪
    daily = build_daily_mood_from_memory_file(memory_path)
    if not daily:
        print("==============================================")
        print(" Universe Singularity · 日终小结 (Phase 3-S02)")
        print("==============================================\n")
        print(f"当前长期情绪文件：{memory_path}")
        print("暂时还没有可用的长期情绪记录。")
        print("可以先用 perception_cli / dialog_cli 说说最近的状态，")
        print("然后再运行 ingest_perception_to_memory 或本脚本。")
        return

    # 4）构造日终小结上下文
    today = date.today()
    days_window = max(1, args.days)

    ctx = build_daily_reflection_context(
        daily,
        today=today,
        days_window=days_window,
    )

    # 5）生成一周情绪小结文本
    weekly_text = generate_weekly_mood_summary_text(ctx.weekly_summary)

    # 6）打印日终小结
    print("==============================================")
    print(" Universe Singularity · 日终小结 (Phase 3-S02)")
    print("==============================================\n")

    # 6.1 写入长期记忆的结果
    print(f"本次从感知仓库写入长期情绪记忆：{len(written_items)} 条")
    print(f"长期情绪文件：{memory_path}\n")

    # 6.2 今日情绪概览
    print("【今日情绪概览】")
    if ctx.today_mood is None:
        print(f"- 今天（{ctx.today.isoformat()}）暂时没有形成完整的情绪聚合记录。")
        print("  可能是今天还没有打卡 / 聊天，也可能是记录较少。")
    else:
        tm = ctx.today_mood
        print(
            f"- 日期：{tm.day.isoformat()} | 整体感觉：{tm.label} | "
            f"平均情绪：{tm.average_score:+.2f} | 样本数：{tm.sample_count}"
        )
    print()

    # 6.3 最近 N 天情绪曲线
    print(f"【最近 {len(ctx.days_used)} 天情绪曲线】")
    if not ctx.days_used:
        print("- 暂无数据。")
    else:
        first_day = ctx.days_used[0].day.isoformat()
        last_day = ctx.days_used[-1].day.isoformat()
        print(f"- 时间范围：{first_day} ~ {last_day}")
        for d in ctx.days_used:
            print(
                f"  {d.day.isoformat()} | {d.label} | "
                f"平均情绪 {d.average_score:+.2f} | 样本数 {d.sample_count}"
            )
    print()

    # 6.4 一周情绪小结
    print("【一周情绪小结】")
    print(weekly_text)
    print()

    # 6.5 今日自我照顾建议
    print("【今日自我照顾建议】")
    if ctx.self_care is None:
        print("- 目前还没有足够的情绪数据来给出建议，有空可以多和我聊聊。")
    else:
        sc = ctx.self_care
        print(f"- 建议模式：{sc.mode}")
        print(f"- 参考天数：{sc.days_considered}")
        print()
        print(sc.message)


if __name__ == "__main__":
    main()
