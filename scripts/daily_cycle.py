from __future__ import annotations

"""
Universe Singularity - Daily Cycle v0

一条命令，串起当前所有「日常协作能力」：

1. 导入本地日记 -> 写入对话事件
2. 收集长期记忆
3. 收集任务（从对话中提取 command 意图）
4. 情绪概览（最近情绪样本 & 每日平均）
5. 规划会话（基于 Workspace / 任务 / 日记）
6. 导出情绪感知待办单 (todo_mood.md)
7. 展示状态面板 & 全局工作空间快照

用法（在项目根目录）：
(.venv) PS D:/UniverseSingularity> python scripts/daily_cycle.py
"""

import sys
from pathlib import Path
from datetime import datetime

# 确保可以 import 到 config / src / scripts 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings  # type: ignore[import]
from config.genome import get_genome  # type: ignore[import]
from src.us_core.utils.logger import setup_logger  # type: ignore[import]

# 导入已有脚本模块，复用它们的 main() 函数
import scripts.import_journal as import_journal  # type: ignore[import]
import scripts.collect_long_term as collect_long_term  # type: ignore[import]
import scripts.collect_tasks as collect_tasks  # type: ignore[import]
import scripts.show_mood as show_mood  # type: ignore[import]
import scripts.planning_session as planning_session  # type: ignore[import]
import scripts.export_todo_mood as export_todo_mood  # type: ignore[import]
import scripts.show_status as show_status  # type: ignore[import]
import scripts.show_workspace as show_workspace  # type: ignore[import]


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("daily_cycle")

    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    print("=== Universe Singularity - Daily Cycle v0 ===")
    print(f"时间: {now_str}")
    print(f"环境: {settings.environment}")
    print(f"胚胎: {genome.embryo.codename}")
    print()

    def run_step(name: str, func) -> None:
        print(f"\n--- 步骤：{name} ---")
        logger.info("Running daily step: %s", name)
        try:
            func()
        except SystemExit:
            # 如果某个脚本内部调用了 sys.exit，避免整个 daily cycle 直接退出
            logger.exception("Step %s triggered SystemExit, ignored.", name)
            print(f"[警告] 步骤 {name} 触发 SystemExit，已忽略。")
        except Exception:
            logger.exception("Step %s failed with exception.", name)
            print(f"[警告] 步骤 {name} 发生错误，已跳过。")

    # 1) 导入日记（如果没有日记文件，会正常提示 0 条）
    run_step("导入本地日记", import_journal.main)

    # 2) 收集长期记忆
    run_step("收集长期记忆", collect_long_term.main)

    # 3) 收集任务
    run_step("收集任务（从对话中提取 command 意图）", collect_tasks.main)

    # 4) 情绪概览
    run_step("情绪概览（Mood Overview）", show_mood.main)

    # 5) 规划会话
    run_step("规划会话（Planning Session）", planning_session.main)

    # 6) 导出情绪感知待办单
    run_step("导出情绪感知待办单 (todo_mood.md)", export_todo_mood.main)

    # 7) 展示状态面板 & 全局工作空间
    run_step("展示状态面板 (Status Dashboard)", show_status.main)
    run_step("展示全局工作空间 (Global Workspace)", show_workspace.main)

    print("\n=== Daily Cycle 完成 ✅ ===")
    logger.info("Daily cycle finished.")


if __name__ == "__main__":
    main()
