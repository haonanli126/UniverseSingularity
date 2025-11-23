#!/usr/bin/env python
"""
交互式：手动指定 mode 来生成一个 focus block 计划（带历史偏好）。

示例（项目根目录）：

    (venv) python scripts/focus_block_planner.py --mode focus --duration-minutes 90 --max-tasks 5
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.engine import (  # type: ignore
    make_focus_block_plan_with_history,
    plan_to_markdown,
)
from us_core.planner.models import FilterSpec  # type: ignore


def _parse_tag_set(value: Optional[str]):
    if not value:
        return None
    tags: List[str] = []
    for part in value.split(","):
        part = part.strip()
        if part:
            tags.append(part)
    return set(tags) if tags else None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Focus block planner (with history preferences)")

    parser.add_argument(
        "--mode",
        choices=["rest", "balance", "focus"],
        required=True,
        help="rest / balance / focus",
    )
    parser.add_argument(
        "--duration-minutes",
        type=int,
        default=90,
        help="本次专注时段总时长（默认 90 分钟）",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=5,
        help="最多选出多少个任务（默认 5）",
    )
    parser.add_argument(
        "--tags-include",
        type=str,
        default=None,
        help="必须包含的标签（逗号分隔）",
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

    args = parser.parse_args(argv)

    filter_spec = FilterSpec(
        include_tags=_parse_tag_set(args.tags_include),
        exclude_tags=_parse_tag_set(args.tags_exclude),
        search=args.search,
    )

    plan = make_focus_block_plan_with_history(
        mode=args.mode,
        max_tasks=args.max_tasks,
        duration_minutes=args.duration_minutes,
        filter_spec=filter_spec,
    )

    md = plan_to_markdown(plan)
    print(md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

