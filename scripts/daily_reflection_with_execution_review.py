#!/usr/bin/env python
"""
增强版日终反思脚本：

- 保留已有 daily reflection 的内容（从 data/journal 里读取最新的 daily_reflection*.md）
- 叠加：今天计划执行情况（基于 data/plans/day_focus_plan_from_mood_* / focus_block_*）
- 同时：把这些执行情况写入 planner_history.jsonl，用于长期偏好学习。
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import sys

# 确保 src 在 sys.path 里
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.execution_review import analyze_plan_file  # type: ignore
from us_core.planner.daily_review import (  # type: ignore
    NamedExecutionSummary,
    aggregate_execution_summaries,
    daily_review_to_markdown,
)
from us_core.planner.preference_memory import append_execution_summary  # type: ignore


def _run_daily_reflection_script() -> None:
    """尝试调用原来的 daily_reflection.py，不要求一定成功。"""
    script_path = PROJECT_ROOT / "scripts" / "daily_reflection.py"
    if not script_path.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            check=False,
        )
    except Exception:
        # 不让异常中断后续流程
        return


def _find_latest_reflection_file(today_only: bool = True) -> Optional[Path]:
    journal_dir = PROJECT_ROOT / "data" / "journal"
    if not journal_dir.exists():
        return None

    pattern = "*daily_reflection*.md"
    candidates = list(journal_dir.glob(pattern))
    if not candidates:
        return None

    if today_only:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_candidates = [p for p in candidates if today_str in p.name]
        if today_candidates:
            candidates = today_candidates

    # 按修改时间排序，取最新
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _find_today_plan_files() -> List[Path]:
    plans_dir = PROJECT_ROOT / "data" / "plans"
    if not plans_dir.exists():
        return []

    today_str = datetime.now().strftime("%Y-%m-%d")

    # 优先使用今天的 plan
    candidates_today = list(plans_dir.glob(f"*{today_str}*.md"))
    if candidates_today:
        return sorted(candidates_today, key=lambda p: p.stat().st_mtime)

    # 没有今天的，就退回到全部 md 文件（可能是之前的）
    all_md = list(plans_dir.glob("*.md"))
    return sorted(all_md, key=lambda p: p.stat().st_mtime)


def main(argv: Optional[List[str]] = None) -> int:
    # 1) 先尝试跑一遍原 daily_reflection，让今天的反思文件生成/更新
    _run_daily_reflection_script()

    # 2) 找到最新的 daily reflection 文件
    reflection_file = _find_latest_reflection_file(today_only=True)
    if reflection_file is not None and reflection_file.exists():
        reflection_text = reflection_file.read_text(encoding="utf-8")
    else:
        reflection_text = "# Daily Reflection\n\n> 今天还没有生成正式的 daily_reflection 内容。\n"

    # 3) 找到今天的 plan 文件
    plan_files = _find_today_plan_files()

    named_summaries: List[NamedExecutionSummary] = []
    for plan_path in plan_files:
        summary = analyze_plan_file(plan_path)

        # 把每个 plan 的执行结果写入历史记忆
        append_execution_summary(plan_name=plan_path.name, summary=summary)

        named_summaries.append(
            NamedExecutionSummary(
                plan_name=plan_path.name,
                summary=summary,
            )
        )

    # 4) 聚合执行情况
    daily_agg = aggregate_execution_summaries(named_summaries)
    review_md = daily_review_to_markdown(daily_agg)

    # 5) 组合成一个新的日终反思文档
    combined_lines: List[str] = []

    combined_lines.append(reflection_text.rstrip())
    combined_lines.append("")
    combined_lines.append("\n---\n")
    combined_lines.append(review_md)

    final_md = "\n".join(combined_lines)

    # 6) 写入新文件
    journal_dir = PROJECT_ROOT / "data" / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = journal_dir / f"daily_reflection_with_execution_review_{timestamp}.md"
    out_path.write_text(final_md, encoding="utf-8")

    print(final_md)
    print()
    print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
