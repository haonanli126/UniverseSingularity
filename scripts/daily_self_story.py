#!/usr/bin/env python
"""
生成一段「Daily Self Story」：

- 使用情绪系统推断 mood_mode；
- 使用自我模型加载 Planner 执行画像；
- 调用 decide_day_mode 得到 final_mode；
- 调用 build_daily_self_story 生成 Markdown；
- 保存到 data/journal/daily_self_story_YYYY-MM-DD.md。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, List
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.mode_resolver import resolve_mode_from_mood_files  # type: ignore
from us_core.self_model.insights import load_planner_insights  # type: ignore
from us_core.self_model.mode_orchestration import decide_day_mode  # type: ignore
from us_core.self_model.narrative import build_daily_self_story  # type: ignore


def main(argv: Optional[List[str]] = None) -> int:
    # 1) 情绪系统：推断今日模式（若无情绪数据，则使用 fallback=balance）
    mood_info = resolve_mode_from_mood_files(preferred_mode="balance")

    # 2) 自我模型：加载 Planner 执行画像
    insights = load_planner_insights()

    # 3) Orchestrator：综合情绪 + 自我模型，得到最终模式
    decision = decide_day_mode(mood_mode=mood_info.mode, insights=insights)

    # 4) 构建自我叙事
    story_md = build_daily_self_story(decision, insights)

    # 控制台打印
    print(story_md)

    # 5) 保存到 journal
    journal_dir = PROJECT_ROOT / "data" / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = journal_dir / f"daily_self_story_{today}.md"
    out_path.write_text(story_md, encoding="utf-8")

    print()
    print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
