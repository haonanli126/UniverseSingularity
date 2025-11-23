#!/usr/bin/env python
"""
根据情绪数据推断 base_mode（rest/balance/focus），
然后为“早 / 午 / 晚”三个 Block 生成一天的任务规划（带历史偏好）。
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
import sys

# 确保 src 在 sys.path 里
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.dayplan import (  # type: ignore
    DayBlockSpec,
    build_day_plan_with_history,
    day_plan_to_markdown,
)
from us_core.planner.mode_resolver import resolve_mode_from_mood_files  # type: ignore
from us_core.planner.models import FilterSpec  # type: ignore


def _parse_tag_set(value: Optional[str]) -> Optional[Set[str]]:
    if not value:
        return None
    tags: List[str] = []
    for part in value.split(","):
        part = part.strip()
        if part:
            tags.append(part)
    return set(tags) if tags else None


def _build_block_specs(
    base_mode: str,
    morning_duration: int,
    afternoon_duration: int,
    evening_duration: int,
    max_tasks_per_block: int,
) -> List[DayBlockSpec]:
    """根据 base_mode 决定早/午/晚各自使用的 mode。"""

    base_mode = base_mode.lower().strip()

    if base_mode == "rest":
        modes = ["rest", "balance", "rest"]
    elif base_mode == "focus":
        modes = ["focus", "focus", "rest"]
    else:
        modes = ["focus", "balance", "rest"]

    return [
        DayBlockSpec(name="morning", mode=modes[0], duration_minutes=morning_duration, max_tasks=max_tasks_per_block),
        DayBlockSpec(name="afternoon", mode=modes[1], duration_minutes=afternoon_duration, max_tasks=max_tasks_per_block),
        DayBlockSpec(name="evening", mode=modes[2], duration_minutes=evening_duration, max_tasks=max_tasks_per_block),
    ]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Day focus plan based on mood (with history preferences)")

    parser.add_argument(
        "--fallback-mode",
        choices=["rest", "balance", "focus"],
        default="balance",
        help="当无法从情绪文件推断 base_mode 时使用的兜底模式，默认 balance",
    )
    parser.add_argument(
        "--morning-duration",
        type=int,
        default=90,
        help="上午 block 时长（分钟），默认 90",
    )
    parser.add_argument(
        "--afternoon-duration",
        type=int,
        default=90,
        help="下午 block 时长（分钟），默认 90",
    )
    parser.add_argument(
        "--evening-duration",
        type=int,
        default=60,
        help="晚上 block 时长（分钟），默认 60",
    )
    parser.add_argument(
        "--max-tasks-per-block",
        type=int,
        default=5,
        help="每个 block 最多任务数，默认 5",
    )
    parser.add_argument(
        "--tags-include",
        type=str,
        default=None,
        help="必须包含的标签（逗号分隔），如：self-care,universe",
    )
    parser.add_argument(
        "--tags-exclude",
        type=str,
        default=None,
        help="排除的标签（逗号分隔）",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="标题/标签关键词过滤（不区分大小写）",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="只在控制台展示，不导出 Markdown 文件",
    )

    args = parser.parse_args(argv)

    # 1) 根据情绪文件推断 base_mode
    info = resolve_mode_from_mood_files(preferred_mode=args.fallback_mode)

    # 2) 构造过滤条件
    filter_spec = FilterSpec(
        include_tags=_parse_tag_set(args.tags_include),
        exclude_tags=_parse_tag_set(args.tags_exclude),
        search=args.search,
    )

    # 3) 构造一天的 block 配置
    block_specs = _build_block_specs(
        base_mode=info.mode,
        morning_duration=args.morning_duration,
        afternoon_duration=args.afternoon_duration,
        evening_duration=args.evening_duration,
        max_tasks_per_block=args.max_tasks_per_block,
    )

    # 4) 生成日计划（带历史偏好）
    day_plan = build_day_plan_with_history(
        base_mode=info.mode,
        block_specs=block_specs,
        filter_spec=filter_spec,
    )

    # 5) 渲染 Markdown
    header_lines: List[str] = []
    header_lines.append("# Day Focus Plan From Mood (with history preferences)")
    header_lines.append("")
    header_lines.append(f"- resolved base_mode: **{info.mode}**")
    header_lines.append(f"- source: `{info.source}`")
    header_lines.append(f"- reason: {info.reason}")
    header_lines.append("")
    header_lines.append(f"- total estimated minutes: **{day_plan.total_estimated_minutes}**")
    header_lines.append("")

    md_body = day_plan_to_markdown(day_plan)
    full_md = "\n".join(header_lines) + "\n" + md_body

    # 控制台打印
    print(full_md)

    # 6) 写入文件
    if not args.no_export:
        plans_dir = PROJECT_ROOT / "data" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"day_focus_plan_from_mood_{info.mode}_{timestamp}.md"
        out_path = plans_dir / filename
        out_path.write_text(full_md, encoding="utf-8")
        print()
        print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

