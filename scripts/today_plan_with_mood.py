from __future__ import annotations

r"""
today_plan_with_mood.py

Phase 3-S04：基于最近几天的情绪和自我照顾模式，给出「今日推荐任务清单」。

功能概述：
  1. 从 data/tasks/tasks.jsonl 读取任务列表
  2. 从长期情绪记忆（perception_long_term.jsonl）构建最近 N 天情绪
  3. 计算 SelfCareSuggestion（rest / balance / focus）
  4. 根据模式推荐今天要优先做的任务（数量随模式变化）
"""

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent

# --- 路径注入，确保能导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception.long_term_view import build_daily_mood_from_memory_file
from us_core.core.self_care import build_self_care_suggestion
from us_core.core.task_recommendation import (
    recommend_task_count,
    recommend_tasks_for_today,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 今日计划（情绪感知版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            r"""
            使用示例：
              1）使用默认路径生成今日推荐任务清单：
                  python .\scripts\today_plan_with_mood.py

              2）只参考最近 3 天的情绪：
                  python .\scripts\today_plan_with_mood.py --days 3

              3）指定自定义任务文件和长期情绪文件：
                  python .\scripts\today_plan_with_mood.py ^
                      --tasks-file path\to\tasks.jsonl ^
                      --memory-file path\to\perception_long_term.jsonl
            """
        ),
    )

    parser.add_argument(
        "--tasks-file",
        type=str,
        default="",
        help="任务 JSONL 文件路径，默认使用 data/tasks/tasks.jsonl。",
    )
    parser.add_argument(
        "--memory-file",
        type=str,
        default="",
        help="长期情绪 JSONL 文件路径，默认使用 data/memory/perception_long_term.jsonl。",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="纳入情绪统计的最大天数（从最近往前数，默认 7 天）。",
    )

    return parser


def _load_tasks_from_jsonl(path: Path) -> list[dict]:
    tasks: list[dict] = []
    if not path.exists():
        return tasks

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    tasks.append(obj)
            except json.JSONDecodeError:
                continue
    return tasks


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1）确定文件路径
    if args.tasks_file:
        tasks_path = Path(args.tasks_file)
    else:
        tasks_path = PROJECT_ROOT / "data" / "tasks" / "tasks.jsonl"

    if args.memory_file:
        memory_path = Path(args.memory_file)
    else:
        memory_path = PROJECT_ROOT / "data" / "memory" / "perception_long_term.jsonl"

    print("==============================================")
    print(" Universe Singularity · 今日计划（情绪感知版）")
    print(" Phase 3-S04 - today_plan_with_mood")
    print("==============================================\n")

    print(f"[信息] 任务文件: {tasks_path}")
    print(f"[信息] 长期情绪: {memory_path}\n")

    # 2）加载任务
    tasks = _load_tasks_from_jsonl(tasks_path)
    if not tasks:
        print("当前任务列表为空，或者任务文件不存在。")
        print("可以先通过对话 / command 生成一些任务，再来看看今日推荐。")
        return

    # 3）构建每日情绪
    daily = build_daily_mood_from_memory_file(memory_path)
    if not daily:
        print("目前还没有可用的长期情绪数据，无法根据状态推荐任务。")
        print("可以先通过 perception_cli / dialog_cli 多和我聊聊，再跑 daily_reflection 或本脚本。")
        return

    days_to_use = max(1, args.days)
    if len(daily) > days_to_use:
        daily = daily[-days_to_use:]

    # 4）构建自我照顾建议
    suggestion = build_self_care_suggestion(daily)
    if suggestion is None:
        print("目前还没有足够的情绪数据来给出自我照顾建议。")
        return

    # 5）根据模式推荐任务
    recommended_tasks = recommend_tasks_for_today(tasks, suggestion)
    planned_count = len(recommended_tasks)
    desired_count = recommend_task_count(suggestion)

    first_day = daily[0].day.isoformat()
    last_day = daily[-1].day.isoformat()

    print("【情绪概况】")
    print(f"- 参考时间范围：{first_day} ~ {last_day}（共 {len(daily)} 天）")
    print(f"- 最近几天的平均情绪分：{suggestion.average_mood:+.2f}")
    print(f"- 自我照顾模式：{suggestion.mode}")
    print()

    print("【今日任务计划】")
    if not recommended_tasks:
        print("- 没有找到处于未完成状态的任务，今天可以更多地关注休息与情绪照顾。")
        return

    print(
        f"- 模式建议任务数：{desired_count} 个；"
        f"实际可用任务数：{len(recommended_tasks)} 个（按优先级排序）。"
    )
    print("- 以下是推荐优先完成的任务：\n")

    for idx, task in enumerate(recommended_tasks, start=1):
        tid = task.get("id") or task.get("task_id") or "?"
        title = task.get("title") or task.get("description") or "(无标题任务)"
        status = task.get("status") or "open"
        priority = task.get("priority", 0)

        print(f"[{idx}] ({tid}) [{status}]  priority={priority}")
        print(f"     {title}")
        tags = task.get("tags") or task.get("labels") or []
        if tags:
            if isinstance(tags, (list, tuple)):
                tag_str = ", ".join(str(t) for t in tags)
            else:
                tag_str = str(tags)
            print(f"     tags: {tag_str}")
        print()


if __name__ == "__main__":
    main()
