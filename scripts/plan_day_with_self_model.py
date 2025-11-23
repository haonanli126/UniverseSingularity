#!/usr/bin/env python
"""
一键生成「带自我模型的日计划」：

- 情绪系统：根据最近情绪推理 mood_mode；
- 自我模型：根据 planner_history + tasks 画像给出 self-model 模式；
- Orchestrator：决定 final_mode；
- Planner：用 final_mode + 历史偏好生成一整天的多 Block 计划。
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.models import FilterSpec  # type: ignore
from us_core.planner.mode_resolver import resolve_mode_from_mood_files  # type: ignore
from us_core.self_model.insights import load_planner_insights  # type: ignore
from us_core.self_model.day_mode_planner import (  # type: ignore
    plan_day_with_mood_and_self_model,
    day_mode_planning_to_markdown,
)


def _parse_tag_set(value: Optional[str]) -> Optional[Set[str]]:
    if not value:
        return None
    tags: List[str] = []
    for part in value.split(","):
        part = part.strip()
        if part:
            tags.append(part)
    return set(tags) if tags else None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a day plan using mood × self-model decision."
    )

    parser.add_argument(
        "--fallback-mode",
        choices=["rest", "balance", "focus"],
        default="balance",
        help="当无法从情绪文件推断 mood_mode 时使用的兜底模式，默认 balance。",
    )
    parser.add_argument(
        "--morning-duration",
        type=int,
        default=90,
        help="上午 block 时长（分钟），默认 90。",
    )
    parser.add_argument(
        "--afternoon-duration",
        type=int,
        default=90,
        help="下午 block 时长（分钟），默认 90。",
    )
    parser.add_argument(
        "--evening-duration",
        type=int,
        default=60,
        help="晚上 block 时长（分钟），默认 60。",
    )
    parser.add_argument(
        "--max-tasks-per-block",
        type=int,
        default=5,
        help="每个 block 最多任务数，默认 5。",
    )
    parser.add_argument(
        "--tags-include",
        type=str,
        default=None,
        help="必须包含的标签（逗号分隔），例如：self-care,universe。",
    )
    parser.add_argument(
        "--tags-exclude",
        type=str,
        default=None,
        help="排除的标签（逗号分隔）。",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="标题/标签关键词过滤（不区分大小写）。",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="只在控制台展示，不导出 Markdown 文件。",
    )

    args = parser.parse_args(argv)

    # 1) 情绪系统：解析 mood_mode
    mood_info = resolve_mode_from_mood_files(preferred_mode=args.fallback_mode)

    # 2) 自我模型：加载执行画像
    insights = load_planner_insights()

    # 3) 过滤条件
    filter_spec = FilterSpec(
        include_tags=_parse_tag_set(args.tags_include),
        exclude_tags=_parse_tag_set(args.tags_exclude),
        search=args.search,
    )

    # 4) 生成日计划（内部会调用 decide_day_mode + build_day_plan_with_history）
    result = plan_day_with_mood_and_self_model(
        mood_mode=mood_info.mode,
        insights=insights,
        morning_duration=args.morning_duration,
        afternoon_duration=args.afternoon_duration,
        evening_duration=args.evening_duration,
        max_tasks_per_block=args.max_tasks_per_block,
        filter_spec=filter_spec,
    )

    md = day_mode_planning_to_markdown(result)

    # 控制台输出
    print(md)

    # 5) 导出 Markdown 文件
    if not args.no_export:
        plans_dir = PROJECT_ROOT / "data" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        final_mode = result.decision.final_mode
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"day_plan_mood_selfmodel_{final_mode}_{timestamp}.md"
        out_path = plans_dir / filename
        out_path.write_text(md, encoding="utf-8")
        print()
        print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
