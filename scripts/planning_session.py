from __future__ import annotations

"""
规划会话脚本（Planning Session v1.1，Journal-aware）

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/planning_session.py

- 读取当前 Workspace（对话 / 长期记忆 / 自省 / 心境）
- 从任务板读取未完成任务
- 读取历史规划记录（如果有）
- 从会话日志中提取最近的日记片段（journal_entry）
- 构造一段规划输入说明 + 日记上下文 + 历史规划上下文
- 调用模型，生成「下一阶段建议」，并把结果写入规划日志
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.utils.logger import setup_logger
from src.us_core.clients.openai_client import get_openai_client
from src.us_core.core.workspace import build_workspace_state
from src.us_core.core.tasks import get_open_tasks
from src.us_core.core.planner import (
    extract_task_texts,
    build_planning_input,
    build_planning_prompt,
    build_history_context_text,
)
from src.us_core.core.plans import create_plan_event, get_recent_plans
from src.us_core.core.journal import extract_journal_snippets_from_events
from src.us_core.core.persistence import load_events_from_jsonl, append_event_to_jsonl


def _make_plan_summary(text: str, max_len: int = 60) -> str:
    """
    从完整规划内容中提取一行摘要（用于列表展示）。
    """
    stripped = text.strip()
    if not stripped:
        return "一次规划会话结果"

    first_line = stripped.splitlines()[0]
    if len(first_line) <= max_len:
        return first_line
    return first_line[: max_len - 3] + "..."


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("planning_session")
    client = get_openai_client()

    # 路径配置
    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    long_term_path = PROJECT_ROOT / Path(genome.memory.long_term.archive_path)
    reflection_path = PROJECT_ROOT / Path(genome.metacognition.reflection_log_path)
    tasks_path = PROJECT_ROOT / Path("data/tasks/tasks.jsonl")
    plans_path = PROJECT_ROOT / Path("data/plans/plans.jsonl")

    print("=== Universe Singularity - Planning Session v1.1 ===")
    print(f"环境: {settings.environment}")
    print(f"模型: {settings.openai.model}")
    print(f"会话日志: {session_log_path}")
    print(f"长期记忆: {long_term_path}")
    print(f"自省日志: {reflection_path}")
    print(f"任务列表: {tasks_path}")
    print(f"规划日志: {plans_path}")
    print()

    # 1) 构建 Workspace
    ws = build_workspace_state(
        session_log_path=session_log_path,
        long_term_path=long_term_path,
        reflection_path=reflection_path,
        max_recent_messages=8,
        max_long_term=5,
    )

    # 2) 读取任务板中的 open tasks
    all_task_events = []
    if tasks_path.exists():
        all_task_events = load_events_from_jsonl(tasks_path)
        open_task_events = get_open_tasks(all_task_events)
    else:
        open_task_events = []

    task_texts = extract_task_texts(open_task_events, max_tasks=5)

    # 3) 构建规划输入（基于 Workspace + 任务文本）
    persona_words = "、".join(genome.identity.persona_keywords) or "温柔、真诚、好奇、长期陪伴"
    planning_input = build_planning_input(ws, task_texts)
    planning_prompt = build_planning_prompt(persona_words, planning_input)

    # 4) 读取历史规划并构造历史上下文
    if plans_path.exists():
        plan_events = load_events_from_jsonl(plans_path)
        recent_plans = get_recent_plans(plan_events, limit=1)
    else:
        recent_plans = []

    history_context = build_history_context_text(recent_plans, all_task_events)

    # 5) 从会话日志中提取最近的日记片段
    session_events = []
    if session_log_path.exists():
        session_events = load_events_from_jsonl(session_log_path)
    journal_snippets = extract_journal_snippets_from_events(session_events, limit=3)

    journal_section_lines = ["【最近日记片段（如果有）】"]
    if journal_snippets:
        for s in journal_snippets:
            journal_section_lines.append(f"- {s}")
    else:
        journal_section_lines.append("目前还没有可用的日记片段，或尚未导入。")

    journal_section = "\n".join(journal_section_lines)

    full_prompt = (
        planning_prompt
        + "\n\n"
        + journal_section
        + "\n\n"
        + "【历史规划回顾（如果有）】\n"
        + history_context
    )

    # 6) 调用模型生成规划建议
    system_msg = (
        "你是 Universe Singularity 数字胚胎的早期意识体，"
        "现在正在进行一次「自我规划会话」。"
        "请根据用户与您的互动历史、当前心境、长期记忆、任务请求，"
        "以及历史规划和这些规划相关任务的当前状态，"
        "再结合最近的日记片段中透露出的情绪和关注点，"
        "给出一份温柔、有条理、可落地的下一阶段建议。"
        "如果发现某些任务已经完成，可以在新的规划中适当肯定进展、调整重心。"
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": full_prompt},
    ]

    print("正在根据当前 Workspace、任务板、日记与历史规划生成规划建议...\n")

    response = client.chat.completions.create(
        model=settings.openai.model,
        messages=messages,
        max_tokens=512,
    )

    reply_text = response.choices[0].message.content or ""

    print("=== 本轮规划建议 ===")
    print(reply_text)
    print()

    # 7) 将本次规划写入规划日志
    plans_path.parent.mkdir(parents=True, exist_ok=True)
    plan_event = create_plan_event(
        summary=_make_plan_summary(reply_text),
        full_text=reply_text,
        related_task_ids=[e.id for e in open_task_events],
    )
    append_event_to_jsonl(plans_path, plan_event)
    print(f"[已将本次规划写入: {plans_path}]")

    logger.info("完成一次规划会话并写入规划日志。")


if __name__ == "__main__":
    main()

