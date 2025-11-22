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

from us_core.perception import (
    InputChannel,
    PerceptionStore,
    build_memory_items_from_perception,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 感知 → 长期记忆 预览 (Phase 2-S01)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）预览最近 20 条感知中会进入长期记忆的条目：
                  python .\\scripts\\preview_perception_to_memory.py --limit 20

              2）只预览心情打卡产生的长期记忆候选：
                  python .\\scripts\\preview_perception_to_memory.py --channel cli_checkin --limit 20

              3）只预览最近 10 条对话中的长期记忆候选：
                  python .\\scripts\\preview_perception_to_memory.py --channel dialog --limit 10
            """
        ),
    )

    parser.add_argument(
        "--channel",
        type=str,
        default="all",
        help="过滤渠道：all（默认）/ cli_checkin / cli_note / dialog 等。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="从感知事件中最多读取多少条做预览（默认 50）。",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    channel = _channel_from_arg(args.channel)
    limit = max(1, args.limit)

    store = PerceptionStore()
    events = list(store.iter_events(channel=channel, limit=limit, reverse=True))

    if not events:
        print("当前没有可用的感知事件。可以先用 perception_cli / dialog_cli 和我聊聊。")
        return

    items = build_memory_items_from_perception(events)

    print(
        f"从最近 {len(events)} 条感知事件中，"
        f"选出了 {len(items)} 条长期记忆候选：\n"
    )

    if not items:
        print("根据当前规则，没有被选中的长期记忆条目。")
        return

    for idx, item in enumerate(items, start=1):
        ts = item.timestamp
        try:
            ts = ts.astimezone()
        except Exception:
            pass
        ts_str = ts.strftime("%Y-%m-%d %H:%M")

        snippet = (item.text or "").replace("\n", " ")
        if len(snippet) > 80:
            snippet = snippet[:77] + "..."

        print(f"[{idx}] {ts_str} intent={item.intent_label}")
        print(f"     {snippet}")
        print()


if __name__ == "__main__":
    main()
