from __future__ import annotations

r"""
export_today_plan_with_mood.py

Phase 3-S06：导出「今日计划（情绪感知版）」到 Markdown 文件。

功能：
  1. 从 data/tasks/tasks.jsonl 读取任务列表
  2. 从长期情绪记忆（perception_long_term.jsonl）构建最近 N 天情绪
  3. 计算 SelfCareSuggestion（rest / balance / focus）
  4. 根据模式推荐今天要优先做的任务
  5. 生成一份 Markdown：
       - 情绪概况
       - 今日推荐任务
       - 其他未完成任务
       - 已完成任务 · 今日小胜利
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.task_store import load_tasks
from us_core.perception.long_term_view import build_daily_mood_from_memory_file
from us_core.core.self_care import build_self_care_suggestion
from us_core.core.task_recommendation import (
    filter_open_tasks,
    recommend_tasks_for_today,
    recommend_task_count,
)


def export_today_plan_markdown(
    tasks_path: Path,
    memory_path: Path,
    days: int,
    output_path: Path,
) -> None:
    # 1) 加载任务 & 情绪数据
    tasks = load_tasks(tasks_path)

    daily = build_daily_mood_from_memory_file(memory_path)
    days = max(1, days)
    if daily and len(daily) > days:
        daily = daily[-days:]

    suggestion = None
    if daily:
        suggestion = build_self_care_suggestion(daily)

    today_str = date.today().isoformat()

    lines: list[str] = []
    lines.append("# Universe Singularity · 今日计划（情绪感知版）")
    lines.append("")
    lines.append(f"- 生成日期：{today_str}")
    lines.append(f"- 任务文件：`{tasks_path}`")
    lines.append(f"- 长期情绪文件：`{memory_path}`")
    lines.append("")

    # 2) 情绪概况
    lines.append("## 情绪概况")
    if suggestion is None or not daily:
        lines.append("")
        lines.append("目前暂时还没有足够的长期情绪数据，")
        lines.append("可以先通过 `perception_cli` / `dialog_cli` 多和我聊聊，再跑 `daily_reflection`。")
    else:
        first_day = daily[0].day.isoformat()
        last_day = daily[-1].day.isoformat()
        lines.append("")
        lines.append(f"- 参考时间范围：{first_day} ~ {last_day}（共 {len(daily)} 天）")
        lines.append(f"- 最近几天的平均情绪分：{suggestion.average_mood:+.2f}")
        lines.append(f"- 自我照顾模式：`{suggestion.mode}`")
        if suggestion.message:
            lines.append("")
            lines.append("> " + suggestion.message.replace("\n", "\n> "))

    # 3) 今日任务计划
    lines.append("")
    lines.append("## 今日任务计划")

    if not tasks:
        lines.append("")
        lines.append("当前任务列表为空，今天可以更多地关注休息与情绪照顾。")
    else:
        open_tasks = filter_open_tasks(tasks)
        done_tasks = [
            t
            for t in tasks
            if str(t.get("status") or "").lower().strip() in {"done", "completed"}
        ]

        recommended: list[dict] = []
        desired_count = 0
        if suggestion is not None and open_tasks:
            recommended = recommend_tasks_for_today(open_tasks, suggestion)
            desired_count = recommend_task_count(suggestion)

        lines.append("")
        if not open_tasks:
            lines.append("目前没有处于未完成状态的任务。")
        else:
            lines.append(f"- 当前未完成任务数：{len(open_tasks)}")
            if suggestion is not None:
                lines.append(
                    f"- 模式建议任务数：{desired_count} 个；"
                    f"本次推荐任务数：{len(recommended)} 个。"
                )

        # 3.1 今日推荐任务
        lines.append("")
        lines.append("### 今日推荐任务")
        if not recommended:
            lines.append("")
            lines.append("目前没有特别需要优先完成的任务，")
            lines.append("可以根据自己的感觉自由选择一两件小事来做。")
        else:
            lines.append("")
            for t in recommended:
                tid = t.get("id") or t.get("task_id") or "?"
                title = t.get("title") or t.get("description") or "(无标题任务)"
                status = t.get("status") or "open"
                priority = t.get("priority", 0)
                lines.append(
                    f"- [ ] {title}  "
                    f"`(id={tid}, status={status}, priority={priority})`"
                )

        # 3.2 其他未完成任务
        lines.append("")
        lines.append("### 其他未完成任务")
        others = [t for t in open_tasks if t not in recommended]
        if not others:
            lines.append("")
            lines.append("除了上面的推荐任务，目前没有其他未完成任务。")
        else:
            lines.append("")
            for t in others:
                tid = t.get("id") or t.get("task_id") or "?"
                title = t.get("title") or t.get("description") or "(无标题任务)"
                status = t.get("status") or "open"
                priority = t.get("priority", 0)
                lines.append(
                    f"- [ ] {title}  "
                    f"`(id={tid}, status={status}, priority={priority})`"
                )

        # 4) 已完成任务 · 今日小胜利
        lines.append("")
        lines.append("## 已完成任务 · 今日小胜利")
        if not done_tasks:
            lines.append("")
            lines.append("目前还没有标记为完成的任务，可以从一件最小的小事开始。")
        else:
            lines.append("")
            for t in done_tasks:
                tid = t.get("id") or t.get("task_id") or "?"
                title = t.get("title") or t.get("description") or "(无标题任务)"
                status = t.get("status") or "done"
                priority = t.get("priority", 0)
                lines.append(
                    f"- [x] {title}  "
                    f"`(id={tid}, status={status}, priority={priority})`"
                )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="导出今日计划（情绪感知版）到 Markdown 文件。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            r"""
            示例：
              1）使用默认路径：
                    python .\scripts\export_today_plan_with_mood.py

              2）只参考最近 3 天情绪，输出到自定义文件：
                    python .\scripts\export_today_plan_with_mood.py ^
                        --days 3 ^
                        --output D:\UniverseSingularity\data\todo\my_today_plan.md
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
        help="纳入情绪统计的最大天数（默认 7）。",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="输出 Markdown 文件路径，默认 data/todo/today_plan_with_mood.md。",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.tasks_file:
        tasks_path = Path(args.tasks_file)
    else:
        tasks_path = PROJECT_ROOT / "data" / "tasks" / "tasks.jsonl"

    if args.memory_file:
        memory_path = Path(args.memory_file)
    else:
        memory_path = PROJECT_ROOT / "data" / "memory" / "perception_long_term.jsonl"

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = PROJECT_ROOT / "data" / "todo" / "today_plan_with_mood.md"

    print("==============================================")
    print(" Universe Singularity · 今日计划导出（情绪感知版）")
    print(" Phase 3-S06 - export_today_plan_with_mood")
    print("==============================================\n")

    print(f"[信息] 任务文件: {tasks_path}")
    print(f"[信息] 长期情绪: {memory_path}")
    print(f"[信息] 输出文件: {output_path}\n")

    export_today_plan_markdown(tasks_path, memory_path, args.days, output_path)

    print(f"[完成] 已生成今日计划 Markdown：{output_path}")


if __name__ == "__main__":
    main()
