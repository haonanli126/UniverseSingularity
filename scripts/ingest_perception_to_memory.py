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

from us_core.perception import InputChannel, PerceptionStore
from us_core.perception.memory_bridge import ingest_perception_events_to_file


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
        description="Universe Singularity · 感知 → 长期记忆 落盘工具 (Phase 2-S02)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）将最近 100 条所有感知事件中值得记住的内容写入长期记忆文件：
                  python .\\scripts\\ingest_perception_to_memory.py --limit 100

              2）只处理心情打卡（cli_checkin），写入长期记忆：
                  python .\\scripts\\ingest_perception_to_memory.py --channel cli_checkin --limit 50

              3）只处理最近 30 条对话中的用户语句：
                  python .\\scripts\\ingest_perception_to_memory.py --channel dialog --limit 30
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
        default=200,
        help="从感知事件中最多读取多少条（默认 200）。None 表示不限制。",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="可选，自定义输出 JSONL 路径；为空时默认写入 data/memory/perception_long_term.jsonl。",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    channel = _channel_from_arg(args.channel)
    limit: int | None = args.limit
    if limit is not None and limit <= 0:
        limit = None

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = PROJECT_ROOT / "data" / "memory" / "perception_long_term.jsonl"

    store = PerceptionStore()

    items = ingest_perception_events_to_file(
        store,
        output_path=output_path,
        channel=channel,
        limit=limit,
    )

    print(
        f"已将 {len(items)} 条长期记忆条目追加写入：{output_path}"
    )
    if not items:
        print("（提示：可以先用 perception_cli / dialog_cli 产生一些感知事件）")


if __name__ == "__main__":
    main()
