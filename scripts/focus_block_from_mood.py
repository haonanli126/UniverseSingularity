#!/usr/bin/env python
"""
根据情绪数据自动选择模式（rest/balance/focus），
然后调用 Planner 器官生成一段 Focus Block 任务计划（带历史偏好）。
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

from us_core.planner.engine import make_focus_block_plan_with_history, plan_to_markdown  # type: ignore
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Focus block planner based on mood (with history preferences)")

    parser.add_argument(
        "--fallback-mode",
        choices=["rest", "balance", "focus"],
        default="balance",
        help="当无法从情绪文件推断 mode 时使用的兜底模式，默认 balance",
    )
    parser.add_argument(
        "--duration-minutes",
        type=int,
        default=90,
        help="本次专注时段总时长（分钟），默认 90",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=5,
        help="最多选出多少个任务，默认 5",
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

    # 1) 根据情绪文件推断 mode
    info = resolve_mode_from_mood_files(preferred_mode=args.fallback_mode)

    # 2) 构造过滤条件
    filter_spec = FilterSpec(
        include_tags=_parse_tag_set(args.tags_include),
        exclude_tags=_parse_tag_set(args.tags_exclude),
        search=args.search,
    )

    # 3) 调用 Planner 器官生成计划（带历史偏好）
    plan = make_focus_block_plan_with_history(
        mode=info.mode,
        max_tasks=args.max_tasks,
        duration_minutes=args.duration_minutes,
        filter_spec=filter_spec,
    )

    # 4) 渲染输出
    header_lines = []
    header_lines.append("# Focus Block From Mood (with history preferences)")
    header_lines.append("")
    header_lines.append(f"- resolved mode: **{info.mode}**")
    header_lines.append(f"- source: `{info.source}`")
    header_lines.append(f"- reason: {info.reason}")
    header_lines.append("")

    md_plan = plan_to_markdown(plan)
    full_md = "\n".join(header_lines) + "\n" + md_plan

    print(full_md)

    if not args.no_export:
        plans_dir = PROJECT_ROOT / "data" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"focus_block_from_mood_{info.mode}_{timestamp}.md"
        out_path = plans_dir / filename
        out_path.write_text(full_md, encoding="utf-8")
        print()
        print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

