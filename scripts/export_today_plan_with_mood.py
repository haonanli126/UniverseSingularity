from __future__ import annotations

r"""
export_today_plan_with_mood.py

Phase 3-S06 + S08：导出「今日计划（情绪 + 标签感知版）」到 Markdown 文件。

功能：
  1. 从 data/tasks/tasks.jsonl 读取任务列表
  2. 从长期情绪记忆（perception_long_term.jsonl）构建最近 N 天情绪
  3. 计算 SelfCareSuggestion（rest / balance / focus）
  4. 根据模式 + 标签（tags）推荐今天要优先做的任务
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
    recommend_task_count,
)


# 与 today_plan_with_mood 中保持一致的标签加成规则
TAG_BOOSTS_BY_MODE: dict[str, dict[str, int]] = {
    "rest": {
        "self-care": 3,
        "self_care": 3,
        "life": 2,
        "健康": 2,
    },
    "balance": {
        "self-care": 2,
        "self_care": 2,
        "life": 2,
        "universe": 2,
        "project": 2,
    },
    "focus": {
        "universe": 3,
        "project": 3,
        "deep-work": 3,
        "deep_work": 3,
        "专注": 2,
    },
}


def compute_task_score(task: dict, suggestion) -> int:
    try:
        base = int(task.get("priority", 0) or 0)
    except (TypeError, ValueError):
        base = 0

    if suggestion is None:
        return base

    mode = (getattr(suggestion, "mode", "") or "").lower()
    boosts = TAG_BOOSTS_BY_MODE.get(mode, {})

    raw_tags = task.get("tags")
    if not raw_tags:
        return base

    if isinstance(raw_tags, (list, tuple)):
        tags = [str(t).lower() for t in raw_tags]
    else:
        tags = [str(raw_tags).lower()]

    bonus = 0
    for t in tags:
        if t in boosts:
            bonus += boosts[t]

    return base + bonus


def choose_tasks_for_today(open_tasks: list[dict], suggestion) -> tuple[list[dict], int]:
    if not open_tasks:
        return [], 0

    if suggestion is not None:
        desired = max(1, recommend_task_count(suggestion))
    else:
        desired = min(3, len(open_tasks))

    scored: list[tuple[int, int, dict]] = []
    for idx, task in enumerate(open_tasks):
        score = compute_task_score(task, suggestion)
        scored.append((score, idx, task))

    scored.sort(key=lambda x: (-x[0], x[1]))
    recommended = [t for _, _, t in scored[:desired]]
    return recommended, desired


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
        if open_tasks:
            recommended, desired_count = choose_tasks_for_today(open_tasks, suggestion)

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
            else:
                lines.append(f"- 本次推荐任务数：{len(recommended)} 个。")

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
                tags = t.get("tags") or []

                tag_str = ""
                if tags:
                    if isinstance(tags, (list, tuple)):
                        tag_val = ", ".join(str(x) for x in tags)
                    else:
                        tag_val = str(tags)
                    tag_str = f", tags={tag_val}"

                lines.append(
                    f"- [ ] {title}  "
                    f"`(id={tid}, status={status}, priority={priority}{tag_str})`"
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
                tags = t.get("tags") or []

                tag_str = ""
                if tags:
                    if isinstance(tags, (list, tuple)):
                        tag_val = ", ".join(str(x) for x in tags)
                    else:
                        tag_val = str(tags)
                    tag_str = f", tags={tag_val}"

                lines.append(
                    f"- [ ] {title}  "
                    f"`(id={tid}, status={status}, priority={priority}{tag_str})`"
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
                tags = t.get("tags") or []

                tag_str = ""
                if tags:
                    if isinstance(tags, (list, tuple)):
                        tag_val = ", ".join(str(x) for x in tags)
                    else:
                        tag_val = str(tags)
                    tag_str = f", tags={tag_val}"

                lines.append(
                    f"- [x] {title}  "
                    f"`(id={tid}, status={status}, priority={priority}{tag_str})`"
                )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="导出今日计划（情绪 + 标签感知版）到 Markdown 文件。",
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
    print(" Phase 3-S06/S08 - export_today_plan_with_mood")
    print("==============================================\n")

    print(f"[信息] 任务文件: {tasks_path}")
    print(f"[信息] 长期情绪: {memory_path}")
    print(f"[信息] 输出文件: {output_path}\n")

    export_today_plan_markdown(tasks_path, memory_path, args.days, output_path)

    print(f"[完成] 已生成今日计划 Markdown：{output_path}")


if __name__ == "__main__":
    main()
