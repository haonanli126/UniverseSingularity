from __future__ import annotations

r"""
today_plan_with_mood.py

Phase 3-S08：情绪 + 标签 感知的今日任务计划。

行为：
  - 从长期情绪中推导自我照顾模式（rest / balance / focus）
  - 从任务列表中选出 open 任务
  - 按「priority + 标签加成」打分，选出适合今天的任务：
      - rest    模式：偏向 self-care / life
      - balance 模式：项目 & 自我照顾平衡
      - focus   模式：偏向 universe / project / deep-work
"""

import argparse
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.core.task_store import load_tasks
from us_core.core.self_care import build_self_care_suggestion
from us_core.core.task_recommendation import filter_open_tasks, recommend_task_count
from us_core.perception.long_term_view import build_daily_mood_from_memory_file


# 不同模式下，标签的加成权重
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
    """
    计算「任务适合作为今天优先项」的分数：
      分数 = priority + (标签加成，按模式不同加权)
    """
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
    """
    根据情绪建议，从 open 任务中挑出「今日推荐任务」。

    返回：
      - recommended: 推荐任务列表
      - desired_count: 模式建议完成任务数
    """
    if not open_tasks:
        return [], 0

    if suggestion is not None:
        desired = max(1, recommend_task_count(suggestion))
    else:
        # 没有情绪建议时，兜底就是最多 3 个
        desired = min(3, len(open_tasks))

    scored: list[tuple[int, int, dict]] = []
    for idx, task in enumerate(open_tasks):
        score = compute_task_score(task, suggestion)
        scored.append((score, idx, task))

    # 按分数从高到低排序，同分则按原始顺序
    scored.sort(key=lambda x: (-x[0], x[1]))
    recommended = [t for _, _, t in scored[:desired]]
    return recommended, desired


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Universe Singularity · 今日任务计划（情绪 + 标签感知版）",
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
    return parser


def _resolve_paths(tasks_file: str, memory_file: str) -> tuple[Path, Path]:
    if tasks_file:
        tasks_path = Path(tasks_file)
    else:
        tasks_path = PROJECT_ROOT / "data" / "tasks" / "tasks.jsonl"

    if memory_file:
        memory_path = Path(memory_file)
    else:
        memory_path = PROJECT_ROOT / "data" / "memory" / "perception_long_term.jsonl"

    return tasks_path, memory_path


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    tasks_path, memory_path = _resolve_paths(args.tasks_file, args.memory_file)

    print("==============================================")
    print(" Universe Singularity · 今日计划（情绪感知版）")
    print(" Phase 3-S04 - today_plan_with_mood (tag-aware)")
    print("==============================================\n")

    print(f"[信息] 任务文件: {tasks_path}")
    print(f"[信息] 长期情绪: {memory_path}\n")

    tasks = load_tasks(tasks_path)

    # --- 情绪部分 ---
    daily = build_daily_mood_from_memory_file(memory_path)
    days = max(1, int(args.days))
    if daily and len(daily) > days:
        daily = daily[-days:]

    suggestion = None
    if daily:
        suggestion = build_self_care_suggestion(daily)

    print("【情绪概况】")
    if suggestion is None or not daily:
        print("- 暂无足够的长期情绪数据，可以先多和我聊聊 / 打卡。")
    else:
        first = daily[0].day.isoformat()
        last = daily[-1].day.isoformat()
        print(f"- 参考时间范围：{first} ~ {last}（共 {len(daily)} 天）")
        print(f"- 最近几天的平均情绪分：{suggestion.average_mood:+.2f}")
        print(f"- 自我照顾模式：{suggestion.mode}")
    print()

    # --- 任务部分 ---
    print("【今日任务计划】")
    if not tasks:
        print("- 当前任务列表为空，今天可以更多地关注休息与情绪照顾。")
        return

    open_tasks = filter_open_tasks(tasks)
    if not open_tasks:
        print("- 当前没有未完成任务，可以把今天完全当作恢复日。")
        return

    recommended, desired_count = choose_tasks_for_today(open_tasks, suggestion)

    print(
        f"- 模式建议任务数：{desired_count} 个；"
        f"实际可用任务数：{len(open_tasks)} 个。"
    )
    print("- 以下是推荐优先完成的任务（已考虑情绪模式与任务标签）：\n")

    if not recommended:
        print("目前没有特别需要优先完成的任务，可以根据感觉自由挑一两件小事。")
        return

    for idx, task in enumerate(recommended, start=1):
        tid = task.get("id") or task.get("task_id") or "?"
        title = task.get("title") or task.get("description") or "(无标题任务)"
        status = task.get("status") or "open"
        priority = task.get("priority", 0)
        tags = task.get("tags") or []

        print(f"[{idx}] ({tid}) [{status}]  priority={priority}")
        print(f"     {title}")
        if tags:
            if isinstance(tags, (list, tuple)):
                tag_str = ", ".join(str(t) for t in tags)
            else:
                tag_str = str(tags)
            print(f"     tags: {tag_str}")
        print()


if __name__ == "__main__":
    main()
