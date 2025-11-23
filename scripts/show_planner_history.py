#!/usr/bin/env python
"""
查看 Planner 历史偏好：

- 从 data/plans/planner_history.jsonl 中读取记录
- 统计每个任务被规划次数 / 完成次数 / 完成率
- 支持按「最容易被拖延」或「最稳定完成」排序展示
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional
import sys

# 确保 src 在 sys.path 里
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.preference_memory import (  # type: ignore
    load_history,
    aggregate_task_stats_from_records,
    attach_task_metadata,
)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Show planner history stats")

    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="展示前多少条任务，默认 20",
    )
    parser.add_argument(
        "--min-planned",
        type=int,
        default=2,
        help="只展示累计被规划次数至少为该值的任务，默认 2",
    )
    parser.add_argument(
        "--sort",
        choices=["worst", "best"],
        default="worst",
        help="按完成率从低到高(worst) 或 从高到低(best) 排序，默认 worst",
    )

    args = parser.parse_args(argv)

    records = load_history()
    if not records:
        print("[info] planner_history.jsonl 还没有任何记录。先运行执行复盘脚本吧。")
        return 0

    stats = aggregate_task_stats_from_records(records)
    if not stats:
        print("[info] 历史记录中暂时没有 task_execution 类型的记录。")
        return 0

    enriched = attach_task_metadata(stats)

    # 过滤：至少被规划 min_planned 次
    filtered = [e for e in enriched if e["times_planned"] >= args.min_planned]
    if not filtered:
        print(f"[info] 没有任务满足 min_planned={args.min_planned} 条件。")
        return 0

    reverse = args.sort == "best"
    filtered.sort(key=lambda e: e["completion_rate"], reverse=reverse)

    top_n = filtered[: args.top]

    print(f"Planner history (sort={args.sort}, min_planned={args.min_planned})")
    print("-" * 90)
    print(f"{'Rate':>6}  {'Planned':>7}  {'Done':>4}  {'Task':<40}  Tags")
    print("-" * 90)

    for entry in top_n:
        rate = f"{entry['completion_rate']*100:5.1f}%"
        planned = entry["times_planned"]
        done = entry["times_completed"]
        title = (entry["title"] or "(unknown)")[:40]
        tags = ", ".join(entry["tags"]) if entry["tags"] else "-"
        print(f"{rate:>6}  {planned:7d}  {done:4d}  {title:<40}  {tags}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
