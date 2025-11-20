from __future__ import annotations

"""
TODO 导出器（TODO Exporter v0）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/export_todo.py

作用：
- 读取任务板（data/tasks/tasks.jsonl）中的未完成任务
- 读取规划日志（data/plans/plans.jsonl）中的最近一次规划
- 将二者导出为一个 markdown 文件：data/todo/todo.md
"""

import sys
from pathlib import Path
from datetime import datetime

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.utils.logger import setup_logger
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.events import EmbryoEvent


def _fmt_ts(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


def _quote_block(text: str) -> str:
    lines = (text or "").rstrip().splitlines()
    if not lines:
        return "> （暂无详细规划内容）"
    return "\n".join("> " + line for line in lines)


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("export_todo")

    tasks_path = PROJECT_ROOT / Path("data/tasks/tasks.jsonl")
    plans_path = PROJECT_ROOT / Path("data/plans/plans.jsonl")
    todo_path = PROJECT_ROOT / Path("data/todo/todo.md")

    print("=== Universe Singularity - TODO Exporter v0 ===")
    print(f"环境: {settings.environment}")
    print(f"任务文件: {tasks_path}")
    print(f"规划文件: {plans_path}")
    print(f"导出路径: {todo_path}")
    print()

    # 1) 读取任务事件
    task_events: list[EmbryoEvent] = []
    if tasks_path.exists():
        task_events = load_events_from_jsonl(tasks_path)

    # 只保留 status == "open" 的任务
    open_tasks: list[EmbryoEvent] = []
    for e in task_events:
        payload = e.payload or {}
        status = str(payload.get("status", "open"))
        if status != "open":
            continue
        open_tasks.append(e)

    # 按时间排序（旧的在前，新的在后）
    open_tasks.sort(key=lambda e: e.timestamp)

    # 2) 读取规划事件（只拿最新一条）
    plan_events: list[EmbryoEvent] = []
    if plans_path.exists():
        plan_events = load_events_from_jsonl(plans_path)

    latest_plan: EmbryoEvent | None = None
    if plan_events:
        plan_events.sort(key=lambda e: e.timestamp)
        latest_plan = plan_events[-1]

    # 3) 生成 markdown 内容
    todo_path.parent.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines: list[str] = []
    lines.append("# Universe Singularity · 温柔待办单")
    lines.append("")
    lines.append(f"- 生成时间: {now_str}")
    lines.append(f"- 环境: {settings.environment}")
    lines.append(f"- 胚胎: {genome.embryo.codename}")
    lines.append("")

    # 未完成任务
    lines.append("## 未完成任务（来自任务板）")
    if not open_tasks:
        lines.append("（目前任务板上没有未完成任务，可以先好好休息一下。）")
    else:
        for e in open_tasks:
            payload = e.payload or {}
            text = str(payload.get("text") or "").strip() or "（无任务文本）"
            intent = str(payload.get("intent") or "command")
            ts_str = _fmt_ts(e.timestamp)
            lines.append(f"- [ ] ({ts_str}, intent={intent}) {text}")
    lines.append("")

    # 最近规划建议
    lines.append("## 最近规划建议（最新一条）")
    if latest_plan is None:
        lines.append("（目前还没有规划记录，你可以先运行 `python scripts/planning_session.py`。）")
    else:
        payload = latest_plan.payload or {}
        summary = str(payload.get("summary") or "").strip()
        full_text = str(payload.get("full_text") or "").rstrip()

        if not summary:
            summary = "一次规划会话结果"

        lines.append(f"**概要：** {summary}")
        lines.append("")
        lines.append("**详细内容：**")
        lines.append("")
        lines.append(_quote_block(full_text))
    lines.append("")

    content = "\n".join(lines)
    todo_path.write_text(content, encoding="utf-8")

    print("导出完成。")
    print(f"你可以在本地打开：{todo_path}")
    logger.info(
        "Exported TODO markdown with %d open tasks and plan=%s",
        len(open_tasks),
        "yes" if latest_plan else "no",
    )


if __name__ == "__main__":
    main()
