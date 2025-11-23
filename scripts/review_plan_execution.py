#!/usr/bin/env python
"""
对某个 Planner 生成的计划（Markdown）进行执行复盘。

用法示例（在项目根目录）：

    # 1）指定一个 plan 文件（必填）
    (venv) python scripts\review_plan_execution.py --plan-file data\\plans\\day_focus_plan_from_mood_balance_2025-11-23_0100.md

    # 2）只在控制台展示，不导出新报告
    (venv) python scripts\review_plan_execution.py --plan-file ... --no-export
"""

from __future__ import annotations

import argparse
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

from us_core.planner.execution_review import (  # type: ignore
    analyze_plan_file,
    execution_summary_to_markdown,
)
from us_core.planner.preference_memory import append_execution_summary  # type: ignore


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Review execution of a plan markdown file")

    parser.add_argument(
        "--plan-file",
        type=str,
        required=True,
        help="Planner 生成的 Markdown 计划文件路径（相对或绝对）",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="只在控制台展示，不导出复盘报告 Markdown 文件",
    )

    args = parser.parse_args(argv)

    plan_path = Path(args.plan_file).expanduser().resolve()
    if not plan_path.exists():
        print(f"[error] plan file not found: {plan_path}")
        return 1

    # 1) 分析执行情况
    summary = analyze_plan_file(plan_path)

    # 1.5) 把结果写入 planner_history.jsonl，作为长期偏好记忆
    append_execution_summary(plan_name=plan_path.name, summary=summary)

    # 2) 渲染 Markdown
    md = execution_summary_to_markdown(summary, plan_file=plan_path)

    # 控制台输出
    print(md)

    # 3) 导出复盘报告
    if not args.no_export:
        plans_dir = PROJECT_ROOT / "data" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"execution_review_{plan_path.stem}_{timestamp}.md"
        out_path = plans_dir / filename
        out_path.write_text(md, encoding="utf-8")
        print()
        print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

