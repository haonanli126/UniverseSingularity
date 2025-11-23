#!/usr/bin/env python
"""
生成「自我画像快照」：

- 基于 planner_history.jsonl + tasks.jsonl
- 统计总体完成率、按标签的完成率
- 输出到 data/self_model/self_model_snapshot_YYYY-MM-DD_HHMM.md
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.self_model.insights import (  # type: ignore
    load_planner_insights,
    insights_to_markdown,
)


def main(argv: Optional[List[str]] = None) -> int:
    insights = load_planner_insights()

    md = insights_to_markdown(insights, top_n=3, min_planned_per_tag=3)

    out_dir = PROJECT_ROOT / "data" / "self_model"
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = out_dir / f"self_model_snapshot_{timestamp}.md"
    out_path.write_text(md, encoding="utf-8")

    print(md)
    print()
    print(f"[saved] {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
