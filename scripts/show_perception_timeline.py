from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent

# --- 确保可以从项目根目录 / src 导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import (
    InputChannel,
    PerceptionStore,
    TimelineItem,
    TimelineSummary,
    build_timeline,
)


def _parse_channel(value: str) -> str:
    """
    将命令行参数里的 channel 映射为真正的 channel 字符串值。

    允许：
      - 'all'：不过滤
      - InputChannel 的 value 值，例如 'cli_checkin'、'cli_note'、'dialog'
    """
    value = value.strip().lower()
    if value == "all":
        return "all"
    return value


def _channel_from_arg(arg_value: str) -> InputChannel | None:
    parsed = _parse_channel(arg_value)
    if parsed == "all":
        return None
    return InputChannel.from_str(parsed)


def _format_ts(ts: datetime) -> str:
    # 转为本地时区，并输出精简格式
    try:
        local_ts = ts.astimezone()
    except Exception:
        local_ts = ts
    return local_ts.strftime("%Y-%m-%d %H:%M")


def _print_summary(summary: TimelineSummary) -> None:
    print(
        f"共 {summary.total_events} 条事件，"
        f"平均情绪评分 {summary.avg_mood_score:+.2f}，"
        f"平均能量 {summary.avg_energy_level:+.2f}"
    )
    if summary.channels_count:
        parts = [
            f"{name}={count}"
            for name, count in sorted(summary.channels_count.items())
        ]
        print("按渠道统计：", ", ".join(parts))
    print()


def _print_timeline(items: list[TimelineItem]) -> None:
    if not items:
        print("当前没有可展示的感知事件。可以先用 perception_cli 或 dialog_cli 产生一些输入。")
        return

    print("按时间从新到旧：\n")
    for idx, item in enumerate(items, start=1):
        ev = item.event
        emo = item.emotion

        ts_str = _format_ts(ev.timestamp)
        channel_name = ev.channel.human_name()

        snippet = ev.content.replace("\n", " ")
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."

        print(
            f"[{idx}] {ts_str} [{channel_name}] "
            f"情绪={emo.sentiment} ({emo.mood_score:+.2f}) "
            f"能量={emo.energy_level:+.2f}"
        )
        print(f"     {snippet}")
        if ev.tags:
            print(f"     tags: {', '.join(ev.tags)}")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 感知时间线浏览器 (Phase 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）查看最近 20 条所有类型的感知事件：
                  python .\\scripts\\show_perception_timeline.py

              2）只看最近 10 条每日心情打卡：
                  python .\\scripts\\show_perception_timeline.py --channel cli_checkin --limit 10

              3）只看最近 5 条对话感知：
                  python .\\scripts\\show_perception_timeline.py --channel dialog --limit 5
            """
        ),
    )

    parser.add_argument(
        "--channel",
        type=str,
        default="all",
        help=(
            "过滤渠道：all（默认）/ cli_checkin / cli_note / dialog 等，"
            "对应 InputChannel 的 value。"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="最多展示多少条事件（默认 20）。",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    channel = _channel_from_arg(args.channel)
    store = PerceptionStore()

    items, summary = build_timeline(
        store,
        channel=channel,
        limit=max(1, args.limit),
    )

    _print_summary(summary)
    _print_timeline(items)


if __name__ == "__main__":
    main()
