#!/usr/bin/env python
"""
综合「情绪」+「自我模型」，给出今天/明天的推荐 base_mode（rest/balance/focus）。

输出示例：

- mood-based mode: focus
- self-model mode: rest
- final suggested mode: balance
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from datetime import datetime
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.mode_resolver import resolve_mode_from_mood_files  # type: ignore
from us_core.self_model.insights import load_planner_insights  # type: ignore
from us_core.self_model.mode_orchestration import decide_day_mode  # type: ignore


def main(argv: Optional[List[str]] = None) -> int:
    # 1) 先看情绪系统给出的模式
    mood_info = resolve_mode_from_mood_files(preferred_mode="balance")

    # 2) 再看 self-model 给出的执行画像
    insights = load_planner_insights()

    # 3) 综合成一个最终模式
    decision = decide_day_mode(mood_mode=mood_info.mode, insights=insights)

    lines: List[str] = []

    lines.append("# Day Mode Decision (Mood × Self-Model)")
    lines.append("")
    lines.append(f"- mood-based mode: **{mood_info.mode}**  (source=`{mood_info.source}`)")
    lines.append(f"- self-model mode: **{decision.self_model_mode or 'N/A'}**")
    lines.append(f"- final suggested base_mode: **{decision.final_mode}**")
    lines.append("")
    lines.append("## Explanation")
    lines.append("")
    lines.append(decision.reason)
    lines.append("")

    if insights.total_planned_events == 0:
        lines.append("> 自我模型还没有任何历史数据。建议先连续使用几天 Planner + 执行复盘，再回来查看这里的建议。")
    else:
        lines.append("## Quick stats from self-model")
        lines.append("")
        lines.append(f"- distinct tasks in history: **{insights.total_tasks}**")
        lines.append(f"- total planned events: **{insights.total_planned_events}**")
        lines.append(f"- total completed events: **{insights.total_completed_events}**")
        lines.append(f"- overall completion rate: **{insights.overall_completion_rate:.2%}**")
    lines.append("")

    md = "\n".join(lines)
    print(md)

    # 4) 也保存一份到 data/self_model 里
    out_dir = PROJECT_ROOT / "data" / "self_model"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = out_dir / f"day_mode_decision_{timestamp}.md"
    out_path.write_text(md, encoding="utf-8")

    print(f"\n[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
