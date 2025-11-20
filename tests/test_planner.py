from __future__ import annotations

"""
测试规划模块（Planner v1）：
"""

from datetime import datetime, timedelta, timezone

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.workspace import WorkspaceState, DialogueMessage, LongTermMemoryItem
from src.us_core.core.planner import (
    summarize_dialogue_for_planning,
    extract_task_texts,
    build_planning_input,
    build_planning_prompt,
    build_history_context_text,
)
from src.us_core.core.plans import PlanItem


def _now():
    return datetime.now(timezone.utc)


def test_summarize_dialogue_for_planning_basic():
    msgs = [
        DialogueMessage(role="user", text="A"),
        DialogueMessage(role="assistant", text="B"),
        DialogueMessage(role="user", text="C"),
        DialogueMessage(role="assistant", text="D"),
    ]

    summary = summarize_dialogue_for_planning(msgs, max_pairs=1)
    # 只应该包含最后一对 C/D
    assert "C" in summary
    assert "D" in summary
    assert "A" not in summary
    assert "B" not in summary


def test_extract_task_texts_order_and_limit():
    t1 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=_now() - timedelta(seconds=10),
        payload={"text": "任务1"},
    )
    t2 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=_now() - timedelta(seconds=5),
        payload={"text": "任务2"},
    )
    t3 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=_now(),
        payload={"text": "任务3"},
    )

    texts = extract_task_texts([t3, t1, t2], max_tasks=2)
    # 应按时间顺序返回 t1, t2
    assert texts == ["任务1", "任务2"]


def test_build_planning_prompt_contains_core_sections():
    now = _now()
    ws = WorkspaceState(
        recent_dialogue=[
            DialogueMessage(role="user", text="我最近有点累"),
            DialogueMessage(role="assistant", text="我在这里陪你。"),
        ],
        long_term_memories=[
            LongTermMemoryItem(
                text="我最近有点累，也有点焦虑。",
                intent_label="emotion",
                timestamp=now - timedelta(seconds=5),
            )
        ],
        last_reflection="我意识到用户最近有些疲惫。",
        last_reflection_time=now - timedelta(seconds=1),
        mood_hint="用户最近多次提到累和焦虑。",
    )

    planning_input = build_planning_input(ws, task_texts=["帮我想一个下一阶段的任务清单，分点列出来。"])
    prompt = build_planning_prompt("温柔、真诚", planning_input)

    # 核心板块应该出现
    assert "【最近心境提示】" in prompt
    assert "【最近对话概览】" in prompt
    assert "【部分长期记忆片段】" in prompt
    assert "【当前待考虑的任务请求】" in prompt

    # 任务内容应该出现在 prompt 中
    assert "下一阶段的任务清单" in prompt
    # 心境提示也应出现
    assert "累和焦虑" in prompt


def test_build_history_context_text_includes_status_and_summary():
    now = _now()
    plan = PlanItem(
        summary="上一轮规划摘要",
        text="这是上一轮规划的完整内容。",
        related_task_ids=["task-1"],
        timestamp=now,
    )

    task_event = EmbryoEvent(
        id="task-1",
        type=EventType.MEMORY,
        payload={
            "kind": "task",
            "status": "done",
            "text": "测试任务",
        },
    )

    context = build_history_context_text([plan], [task_event])

    assert "上一轮规划概览" in context
    assert "上一轮规划摘要" in context
    assert "测试任务" in context
    assert "[done]" in context
