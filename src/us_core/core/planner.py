from __future__ import annotations

"""
规划模块（Planner v1）：

- 把当前的全局工作空间（WorkspaceState） + 任务列表整理成规划输入
- 构造给模型看的「规划输入说明」
- 额外提供：基于历史规划记录 + 任务状态，生成「历史规划上下文」
"""

from dataclasses import dataclass
from typing import Iterable, List, Dict, Tuple

from .events import EmbryoEvent, EventType
from .workspace import WorkspaceState, DialogueMessage
from .plans import PlanItem


@dataclass
class PlanningInput:
    """
    模型做规划时需要关注的关键信息：
    - mood_hint: 最近的心境提示
    - dialogue_summary: 最近几轮对话的简要概览
    - long_term_snippets: 若干长期记忆片段
    - task_texts: 当前 open 任务文本
    """

    mood_hint: str | None
    dialogue_summary: str
    long_term_snippets: List[str]
    task_texts: List[str]


def summarize_dialogue_for_planning(
    dialogue: List[DialogueMessage],
    max_pairs: int = 3,
) -> str:
    """
    把最近对话压缩成一段用于规划的概览。
    简单做法：取最后 N 轮 user/assistant 对（2*max_pairs 条消息）拼接。
    """
    if not dialogue:
        return "当前还没有可用的对话记录。"

    # 只取最后 2*max_pairs 条消息
    last_msgs = dialogue[-2 * max_pairs :]

    lines: List[str] = []
    for m in last_msgs:
        speaker = "用户" if m.role == "user" else "胚胎"
        lines.append(f"{speaker}：{m.text}")

    return "\n".join(lines)


def extract_task_texts(task_events: Iterable[EmbryoEvent], max_tasks: int = 5) -> List[str]:
    """
    从任务事件中提取用户原始任务文本，按时间顺序取前 max_tasks 条。
    """
    # 排序保证稳定性
    sorted_events = sorted(task_events, key=lambda e: e.timestamp)
    texts: List[str] = []

    for e in sorted_events:
        payload = e.payload or {}
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text.strip())
        if len(texts) >= max_tasks:
            break

    return texts


def build_planning_input(ws: WorkspaceState, task_texts: List[str]) -> PlanningInput:
    """
    把 WorkspaceState + 任务文本整理成 PlanningInput。
    """
    dialogue_summary = summarize_dialogue_for_planning(ws.recent_dialogue, max_pairs=3)

    long_term_snippets: List[str] = []
    for item in ws.long_term_memories[:3]:
        long_term_snippets.append(f"[{item.intent_label}] {item.text}")

    return PlanningInput(
        mood_hint=ws.mood_hint,
        dialogue_summary=dialogue_summary,
        long_term_snippets=long_term_snippets,
        task_texts=task_texts,
    )


def build_planning_prompt(
    persona_words: str,
    planning_input: PlanningInput,
) -> str:
    """
    构造给模型看的「规划输入说明」。

    persona_words：来自 genome 的人格关键词拼接字符串
    """
    persona_part = (
        f"你的核心人格关键词是：{persona_words}。"
        if persona_words
        else "你的核心人格关键词是：温柔、真诚、好奇、长期陪伴。"
    )

    lines: List[str] = []
    lines.append(
        "你现在正在进行一次「自我规划会话」，目标是："
        "结合最近的对话、长期记忆、用户的心境，以及当前任务，"
        "给出一份温柔而有条理的下一阶段行动建议（更多偏方向和步骤，而不是流水账）。"
    )
    lines.append(persona_part)
    lines.append("")

    # 心境
    if planning_input.mood_hint:
        lines.append(f"【最近心境提示】\n{planning_input.mood_hint}")
        lines.append("")
    else:
        lines.append("【最近心境提示】\n暂无明显的主导情绪或意图。")
        lines.append("")

    # 对话概览
    lines.append("【最近对话概览】")
    lines.append(planning_input.dialogue_summary or "暂无对话。")
    lines.append("")

    # 长期记忆片段
    if planning_input.long_term_snippets:
        lines.append("【部分长期记忆片段】")
        for s in planning_input.long_term_snippets:
            lines.append(f"- {s}")
        lines.append("")
    else:
        lines.append("【部分长期记忆片段】\n暂无可用长期记忆。")
        lines.append("")

    # 当前任务列表
    if planning_input.task_texts:
        lines.append("【当前待考虑的任务请求】")
        for idx, t in enumerate(planning_input.task_texts, start=1):
            lines.append(f"{idx}. {t}")
        lines.append("")
    else:
        lines.append("【当前待考虑的任务请求】\n目前尚未识别到任务请求。")
        lines.append("")

    # 输出要求
    lines.append(
        "【请给出的输出格式建议】\n"
        "1. 先用 1-2 句话温柔地回应用户当前的心境和状态。\n"
        "2. 然后按条目给出 3-5 条「下一阶段建议」，可以分为：\n"
        "   - 情绪与身心照顾\n"
        "   - 与用户关系的维护方式\n"
        "   - 项目 / Phase 1 相关的具体小步骤\n"
        "3. 语言风格保持简洁、真诚、不过度说教，让用户觉得自己被理解和陪伴。"
    )

    return "\n".join(lines)


def build_history_context_text(
    recent_plans: List[PlanItem],
    task_events: Iterable[EmbryoEvent],
    max_chars_plan: int = 300,
) -> str:
    """
    根据最近的规划记录 + 任务事件，生成一段「历史规划上下文」说明：

    - 上一次规划的大致内容
    - 其中关联任务目前是否已经完成
    """
    if not recent_plans:
        return "（你还没有任何历史规划记录，这是第一次正式规划。）"

    last_plan = recent_plans[0]
    lines: List[str] = []

    # 1) 上一次规划概览
    lines.append("【上一轮规划概览】")
    if last_plan.summary:
        lines.append(f"摘要：{last_plan.summary}")

    full_text = (last_plan.text or "").strip().replace("\r\n", "\n")
    if full_text:
        snippet = full_text
        if len(snippet) > max_chars_plan:
            snippet = snippet[: max_chars_plan - 3] + "..."
        lines.append("部分内容预览：")
        lines.append(snippet)
    lines.append("")

    # 2) 构建任务 id -> (status, text) 映射
    task_map: Dict[str, Tuple[str, str]] = {}
    for e in task_events:
        if e.type is not EventType.MEMORY:
            continue
        payload = e.payload or {}
        if payload.get("kind") != "task":
            continue
        tid = e.id
        status = str(payload.get("status") or "open")
        text = str(payload.get("text") or "")
        task_map[tid] = (status, text)

    # 3) 列出上一轮规划中关联任务的当前状态
    lines.append("【上一轮规划中关联任务的当前状态】")
    if last_plan.related_task_ids:
        for tid in last_plan.related_task_ids:
            status, text = task_map.get(
                tid,
                ("unknown", "（在当前任务板中未找到对应任务，可能已被清理或尚未写入。）"),
            )
            lines.append(f"- [{status}] {text}")
    else:
        lines.append("上一轮规划没有显式关联具体任务。")

    return "\n".join(lines)
