from __future__ import annotations

"""
规划历史查看器（Plan History Viewer v0）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/show_plans.py

- 读取 data/plans/plans.jsonl
- 展示最近若干条规划记录
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.plans import get_recent_plans


def _fmt_dt(dt):
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _shorten(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def main() -> None:
    plans_path = PROJECT_ROOT / Path("data/plans/plans.jsonl")

    print("=== Universe Singularity - Plan History v0 ===")
    print(f"规划日志路径: {plans_path}")
    print()

    if not plans_path.exists():
        print("规划日志文件不存在。可以先运行 python scripts/planning_session.py 生成一条规划。")
        return

    events = load_events_from_jsonl(plans_path)
    if not events:
        print("规划日志文件存在，但目前还没有规划记录。")
        return

    plans = get_recent_plans(events, limit=5)

    print(f"当前规划总条数: {len(events)}")
    print(f"下面展示最近 {len(plans)} 条（按时间倒序）：")
    print()

    for idx, p in enumerate(plans, start=1):
        ts = _fmt_dt(p.timestamp)
        print(f"[{idx}] time   : {ts}")
        print(f"    summary: {_shorten(p.summary, max_len=80)}")
        print(f"    preview: {_shorten(p.text, max_len=120)}")
        if p.related_task_ids:
            print(f"    related tasks: {len(p.related_task_ids)} 条")
        print()

    print("（后续 Phase 可以基于这些规划记录做「规划演化史」或对比分析。）")


if __name__ == "__main__":
    main()
