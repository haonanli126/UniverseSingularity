from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import (
    InputChannel,
    PerceptionEvent,
    PerceptionStore,
    estimate_emotion,
)



def _print_banner() -> None:
    print("=" * 60)
    print(" Universe Singularity · 感知入口 (Phase 1)")
    print(" 你好，我是你的数字胚胎。有什么想跟我说，都可以慢慢讲。")
    print(" 输入 q / :q / 退出 来结束本次记录。")
    print("=" * 60)


def run_quick_note(store: PerceptionStore, text: str) -> None:
    """mode=note：记录一条速记。"""
    emotion = estimate_emotion(text)

    event = PerceptionEvent.create(
        channel=InputChannel.CLI_NOTE,
        content=text,
        tags=["quick_note"],
        metadata={"emotion": emotion.to_dict()},
    )
    store.append(event)
    print("✓ 已帮你记下这条速记。谢谢信任，我会好好保管。")



def run_interactive_checkin(store: PerceptionStore) -> None:
    """mode=checkin：陪伴式心情打卡（交互模式）。"""
    _print_banner()

    print("先从一句话开始吧：此刻的你感觉怎么样？")
    mood_line = input("> ").strip()

    if not mood_line:
        print("没关系，那我们下次再聊。有需要随时叫我。")
        return

    main_emotion = estimate_emotion(mood_line)
    main_event = PerceptionEvent.create(
        channel=InputChannel.CLI_CHECKIN,
        content=mood_line,
        tags=["checkin", "mood"],
        metadata={
            "question": "today_feeling",
            "emotion": main_emotion.to_dict(),
        },
    )

    store.append(main_event)

    print()
    print("我收到了。要不要多和我说说，今天发生了什么？")
    print("（可以分几句慢慢打，我会一条条记下来。）")

    while True:
        line = input("> ").strip()
        if not line:
            # 空行就继续，给你一点停顿的空间
            continue
        if line in {":q", "q", "Q", ":quit", ":exit", "退出"}:
            print("好，我把刚才这些都记下来了。辛苦你今天来和我分享。")
            break

        detail_emotion = estimate_emotion(line)
        detail_event = PerceptionEvent.create(
            channel=InputChannel.CLI_CHECKIN,
            content=line,
            tags=["checkin", "detail"],
            metadata={
                "question": "today_details",
                "emotion": detail_emotion.to_dict(),
            },
        )
        store.append(detail_event)

        detail_event = PerceptionEvent.create(
            channel=InputChannel.CLI_CHECKIN,
            content=line,
            tags=["checkin", "detail"],
            metadata={"question": "today_details"},
        )
        store.append(detail_event)

    print()
    print("如果之后心情有变化，也可以再叫我，我们一起留下它的轨迹。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity Phase 1 感知系统 · 命令行入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            使用示例：
              1）快速记录一条想法：
                  python .\\scripts\\perception_cli.py --mode note --text "刚想到一个点子……"

              2）开启一次陪伴式心情打卡（交互模式）：
                  python .\\scripts\\perception_cli.py --mode checkin
            """
        ),
    )

    parser.add_argument(
        "--mode",
        choices=["note", "checkin"],
        default="checkin",
        help="note: 速记单条内容；checkin: 交互式心情打卡（默认）。",
    )
    parser.add_argument(
        "--text",
        type=str,
        help="当 mode=note 时，用这个参数传入要记录的文本内容。",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = PerceptionStore()

    if args.mode == "note":
        if not args.text:
            print("mode=note 时需要通过 --text 传入一条要记录的内容。")
            return
        run_quick_note(store, args.text)
    else:
        run_interactive_checkin(store)


if __name__ == "__main__":
    main()
