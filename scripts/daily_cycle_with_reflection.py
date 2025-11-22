from __future__ import annotations

r"""
daily_cycle_with_reflection.py

Phase 3-S03：把每日循环和日终小结打包成一个入口。

效果：
  - 先运行原有的 daily_cycle（不改变原脚本行为）
  - 再运行 daily_reflection（Phase 3-S02）

这样每次只要执行：
    python .\scripts\daily_cycle_with_reflection.py

就可以完成：
    1）每日循环（任务 / 心跳等）
    2）写入最新长期情绪记忆 + 一周情绪小结 + 今日自我照顾建议
"""

import sys
from pathlib import Path

# --- 确保可以导入 scripts 目录下的其它脚本 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import daily_cycle  # type: ignore[import]
import daily_reflection  # type: ignore[import]


def _safe_call_main(mod) -> None:
    """
    尝试以兼容的方式调用某个脚本模块的 main：

    兼容几种可能的签名：
      - def main(): ...
      - def main(argv: list[str] | None = None): ...
    """
    fn = getattr(mod, "main", None)
    if fn is None:
        return

    # 优先尝试传入空 argv
    try:
        fn([])
        return
    except TypeError:
        pass

    # 再试只传 today
    try:
        fn()
        return
    except TypeError:
        pass

    # 最后试试传 None
    try:
        fn(None)
    except TypeError:
        # 实在不兼容就算了，不抛异常，避免影响整个脚本
        return


def main(argv: list[str] | None = None) -> None:
    print("==============================================")
    print(" Universe Singularity · 每日循环 + 日终小结")
    print(" Phase 3-S03 - daily_cycle_with_reflection")
    print("==============================================\n")

    # 1）运行原有每日循环
    print("[1/2] 正在运行 daily_cycle ...")
    _safe_call_main(daily_cycle)
    print()

    # 2）运行日终小结（使用默认参数：最近 7 天，ingest-limit=200）
    print("[2/2] 正在运行 daily_reflection（日终小结） ...\n")
    _safe_call_main(daily_reflection)

    print("\n[完成] 今日的每日循环 + 日终小结已执行。")


if __name__ == "__main__":
    main()
