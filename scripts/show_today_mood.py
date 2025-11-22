from __future__ import annotations

import argparse
import sys
from datetime import datetime, date
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
    DailyMoodSummary,
    build_daily_mood_summary,
)


def _parse_channel(value: str) -> str:
    value = value.strip().lower()
    if value == "all":
        return "all"
    return value


def _channel_from_arg(arg_value: str) -> InputChannel | None:
    parsed = _parse_channel(arg_value)
    if parsed == "all":
        return None
    return InputChannel.from_str(parsed)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        print(f"[警告] 无法解析日期 {value}，应为 YYYY-MM-DD 格式，将默认使用今天。")
        return None


def _print_summary(summary: DailyMoodSummary) -> None:
    date_str = summary.date.strftime("%Y-%m-%d")
    print(f"日期：{date_str}")

    if summary.total_events == 0:
        print("今天暂无感知事件。可以先用 perception_cli 或 dialog_cli 和我聊聊。")
        return

    channels_part = ", ".join(
        f"{name}={count}"
        for name, count in sorted(summary.channels_count.items())
    ) or "无"

    sentiments_part = ", ".join(
        f"{name}={count}"
        for name, count in sorted(summary.sentiment_counts.items())
    ) or "无"

    print(f"总事件数：{summary.total_events}（按渠道：{channels_part}）")
    print(f"情绪分布：{sentiments_part}")
    print(
        f"平均情绪：{summary.avg_mood_score:+.2f}（越接近 1 越积极）\n"
        f"平均能量：{summary.avg_energy_level:+.2f}（越接近 1 能量越高）"
    )
    print()


def _print_samples(summary: DailyMoodSummary) -> None:
    if not summary.samples:
        print("暂时没有明显偏强的情绪片段，可以理解为今天整体比较平稳。")
        return

    print("代表性片段：（按情绪强度排序）\n")
    for idx, sample in enumerate(summary.samples, start=1):
        ev = sample.event
        emo = sample.emotion

        ts = ev.timestamp
        if ts.tzinfo is not None:
            try:
                ts = ts.astimezone()
            except Exception:
                pass
        time_str = ts.strftime("%H:%M")

        snippet = ev.content.replace("\n", " ")
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."

        print(
            f"[{idx}] {time_str} "
            f"情绪={emo.sentiment} ({emo.mood_score:+.2f}) "
            f"能量={emo.energy_level:+.2f}"
        )
        print(f"     {snippet}")
        if ev.tags:
            print(f"     tags: {', '.join(ev.tags)}")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 今日心情小结 (Phase 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）查看今天所有渠道的心情小结：
                  python .\\scripts\\show_today_mood.py

              2）只看今天的心情打卡（cli_checkin）：
                  python .\\scripts\\show_today_mood.py --channel cli_checkin

              3）查看指定日期（例如 2025-11-20）的心情小结：
                  python .\\scripts\\show_today_mood.py --date 2025-11-20
            """
        ),
    )

    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="指定日期（YYYY-MM-DD），为空时使用今天。",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="all",
        help="过滤渠道：all（默认）/ cli_checkin / cli_note / dialog 等。",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    target_date = _parse_date(args.date)
    channel = _channel_from_arg(args.channel)

    store = PerceptionStore()
    summary = build_daily_mood_summary(
        store,
        target_date=target_date,
        channel=channel,
    )

    _print_summary(summary)
    if summary.total_events > 0:
        _print_samples(summary)


if __name__ == "__main__":
    main()
