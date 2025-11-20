from __future__ import annotations

"""
情绪感知 TODO 导出器（Mood-aware TODO Exporter v0）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/export_todo_mood.py

作用：
- 读取任务板（data/tasks/tasks.jsonl）中的未完成任务
- 读取规划日志（data/plans/plans.jsonl）中的最新规划
- 结合最近的情绪信息（长期记忆 + 日记），给出「适合当下状态的推荐任务」
- 导出为 markdown：data/todo/todo_mood.md
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
from src.us_core.core.events import EmbryoEvent
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.workspace import build_workspace_state
from src.us_core.core.mood import (
    build_mood_samples_from_long_term,
    build_mood_samples_from_journal_events,
    aggregate_daily_mood,
)


def _fmt_ts(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M")


def _quote_block(text: str) -> str:
    lines = (text or "").rstrip().splitlines()
    if not lines:
        return "> （暂无详细规划内容）"
    return "\n".join("> " + line for line in lines)


def mood_hint(mood_score: float | None) -> str:
    """
    根据情绪分数给一点人类可读的提示。
    """
    if mood_score is None:
        return "目前没有足够的情绪样本，我先用一个中性的节奏给你安排一些轻量任务。"
    if mood_score <= -1.0:
        return "你最近的情绪有点偏负，我只给你安排一两件很轻量的小事情，其他都可以以后再说。"
    if -1.0 < mood_score < 0.0:
        return "状态略微有点低落，我们挑少量、压力很小的小任务就好。"
    if 0.0 <= mood_score < 1.0:
        return "整体比较平稳，可以安排几件适中强度的小任务。"
    return "你最近状态还不错，可以多选几件你愿意推进的任务，但也不用勉强自己。"


def select_recommended_tasks(
    mood_score: float | None,
    open_tasks: list[EmbryoEvent],
) -> list[EmbryoEvent]:
    """
    根据情绪分数，从未完成任务中挑出「推荐任务」列表。

    这里只控制「数量」，不控制任务内容本身：
    - 情绪明显偏负（<= -1.0）：1 条
    - 略偏负（-1.0 ~ 0）：2 条
    - 中性（0 ~ 1）：3 条
    - 明显偏正（>= 1）：最多 5 条
    - 没有情绪样本：默认 3 条
    """
    if not open_tasks:
        return []

    if mood_score is None:
        max_count = 3
    elif mood_score <= -1.0:
        max_count = 1
    elif -1.0 < mood_score < 0.0:
        max_count = 2
    elif 0.0 <= mood_score < 1.0:
        max_count = 3
    else:
        max_count = 5

    if max_count > len(open_tasks):
        max_count = len(open_tasks)

    return open_tasks[:max_count]


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("export_todo_mood")

    tasks_path = PROJECT_ROOT / Path("data/tasks/tasks.jsonl")
    plans_path = PROJECT_ROOT / Path("data/plans/plans.jsonl")
    todo_path = PROJECT_ROOT / Path("data/todo/todo_mood.md")

    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    long_term_path = PROJECT_ROOT / Path(genome.memory.long_term.archive_path)
    reflection_path = PROJECT_ROOT / Path(genome.metacognition.reflection_log_path)

    print("=== Universe Singularity - Mood-aware TODO Exporter v0 ===")
    print(f"环境: {settings.environment}")
    print(f"任务文件: {tasks_path}")
    print(f"规划文件: {plans_path}")
    print(f"会话日志: {session_log_path}")
    print(f"长期记忆: {long_term_path}")
    print(f"导出路径: {todo_path}")
    print()

    # 1) 读取任务事件，筛选 open
    task_events: list[EmbryoEvent] = []
    if tasks_path.exists():
        task_events = load_events_from_jsonl(tasks_path)

    open_tasks: list[EmbryoEvent] = []
    for e in task_events:
        payload = e.payload or {}
        status = str(payload.get("status", "open"))
        if status != "open":
            continue
        open_tasks.append(e)

    open_tasks.sort(key=lambda e: e.timestamp)

    # 2) 读取规划事件（只拿最新一条）
    plan_events: list[EmbryoEvent] = []
    if plans_path.exists():
        plan_events = load_events_from_jsonl(plans_path)

    latest_plan: EmbryoEvent | None = None
    if plan_events:
        plan_events.sort(key=lambda e: e.timestamp)
        latest_plan = plan_events[-1]

    # 3) 计算最近情绪（长期记忆 + 日记）
    mood_score: float | None = None
    mood_label_text = "未知"
    mood_meta_line = "暂无足够情绪样本"

    # Workspace 给我们长期记忆
    ws = build_workspace_state(
        session_log_path=session_log_path,
        long_term_path=long_term_path,
        reflection_path=reflection_path,
        max_recent_messages=8,
        max_long_term=100,
    )
    lt_samples = build_mood_samples_from_long_term(ws.long_term_memories)

    journal_events: list[EmbryoEvent] = []
    if session_log_path.exists():
        journal_events = load_events_from_jsonl(session_log_path)
    journal_samples = build_mood_samples_from_journal_events(journal_events)

    all_samples = lt_samples + journal_samples
    all_samples.sort(key=lambda s: s.timestamp)

    if all_samples:
        daily = aggregate_daily_mood(all_samples)
        last = daily[-1]
        mood_score = last.average_score
        mood_label_text = last.label
        mood_meta_line = (
            f"{last.day.isoformat()}  avg={last.average_score:.2f}  "
            f"({last.label})  samples={last.sample_count}"
        )

    # 4) 基于情绪选择推荐任务
    recommended_tasks = select_recommended_tasks(mood_score, open_tasks)

    # 5) 生成 markdown 内容
    todo_path.parent.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines: list[str] = []
    lines.append("# Universe Singularity · 情绪感知待办单")
    lines.append("")
    lines.append(f"- 生成时间: {now_str}")
    lines.append(f"- 环境: {settings.environment}")
    lines.append(f"- 胚胎: {genome.embryo.codename}")
    lines.append("")
    lines.append("## 当前情绪概览")
    lines.append("")
    lines.append(f"- 最近情绪：{mood_label_text}")
    lines.append(f"- 详细：{mood_meta_line}")
    lines.append("")
    lines.append(mood_hint(mood_score))
    lines.append("")

    # 推荐任务
    lines.append("## 适合当下状态的推荐任务")
    lines.append("")
    if not recommended_tasks:
        lines.append("（目前没有需要推荐的任务，或者我们可以暂时什么都不做，好好歇一歇。）")
    else:
        for e in recommended_tasks:
            payload = e.payload or {}
            text = str(payload.get("text") or "").strip() or "（无任务文本）"
            intent = str(payload.get("intent") or "command")
            ts_str = _fmt_ts(e.timestamp)
            lines.append(f"- [ ] ({ts_str}, intent={intent}) {text}")
    lines.append("")

    # 全部未完成任务
    lines.append("## 全部未完成任务（参考）")
    if not open_tasks:
        lines.append("（任务板上暂时没有未完成任务。）")
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
        "Exported mood-aware TODO markdown with %d open tasks, %d recommended, mood=%s",
        len(open_tasks),
        len(recommended_tasks),
        "None" if mood_score is None else f"{mood_score:.2f}",
    )


if __name__ == "__main__":
    main()
