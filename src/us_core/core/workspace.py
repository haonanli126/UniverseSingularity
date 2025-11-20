from __future__ import annotations

"""
全局工作空间快照（Global Workspace Snapshot v0）

负责把当前「心智状态」聚合成一个结构：

- 最近对话若干条（短期工作记忆）
- 最近若干条长期记忆（已经归档的重要内容）
- 最近一次自省内容及时间
- 粗略的「心境提示」：最近主要在聊什么 / 哪类 intent 为主
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from collections import Counter

from .events import EmbryoEvent, EventType
from .persistence import load_events_from_jsonl
from .recall import events_to_dialogue
from .long_term import get_recent_archive_events


@dataclass
class DialogueMessage:
    role: str
    text: str


@dataclass
class LongTermMemoryItem:
    text: str
    intent_label: str
    timestamp: datetime


@dataclass
class WorkspaceState:
    recent_dialogue: List[DialogueMessage]
    long_term_memories: List[LongTermMemoryItem]
    last_reflection: Optional[str]
    last_reflection_time: Optional[datetime]
    mood_hint: Optional[str]


def _compute_mood_hint(events: Iterable[EmbryoEvent]) -> Optional[str]:
    """
    根据最近一段会话中的 intent，给出一个简单的「心境提示」。
    """
    counts: Counter[str] = Counter()
    last_emotion_text: Optional[str] = None

    for e in events:
        if e.type is not EventType.PERCEPTION:
            continue
        payload = e.payload or {}
        intent = payload.get("intent") or {}
        label = intent.get("label")
        if not isinstance(label, str):
            continue

        counts[label] += 1

        if label == "emotion":
            text = payload.get("text")
            if isinstance(text, str) and text:
                last_emotion_text = text

    if not counts:
        return None

    top_label, _ = counts.most_common(1)[0]

    if top_label == "emotion":
        return last_emotion_text or "用户最近多次表达情绪。"
    if top_label == "project":
        return "最近主要在讨论项目 / 宇宙奇点相关话题。"
    if top_label == "command":
        return "最近更多是在请求你执行具体任务或输出。"
    if top_label == "meta":
        return "最近在谈论你们之间的关系、记忆或你的状态。"
    # chat / unknown 等
    return None


def build_workspace_state(
    session_log_path: Path,
    long_term_path: Path,
    reflection_path: Path,
    max_recent_messages: int = 8,
    max_long_term: int = 5,
) -> WorkspaceState:
    """
    聚合当前「意识工作空间」快照。
    """
    # 1) 最近对话（短期记忆）
    if session_log_path.exists():
        session_events = load_events_from_jsonl(session_log_path)
    else:
        session_events = []

    dialogue_dicts = events_to_dialogue(
        session_events,
        max_messages=max_recent_messages,
    )
    recent_dialogue = [
        DialogueMessage(role=m["role"], text=m["text"]) for m in dialogue_dicts
    ]

    # 2) 最近长期记忆（长时记忆摘要）
    if long_term_path.exists():
        long_term_events = load_events_from_jsonl(long_term_path)
    else:
        long_term_events = []

    long_term_recent = get_recent_archive_events(
        long_term_events, limit=max_long_term
    )
    long_term_memories: List[LongTermMemoryItem] = []
    for e in long_term_recent:
        payload = e.payload or {}
        text = str(payload.get("text") or "")
        intent = payload.get("intent") or {}
        label = str(intent.get("label") or "unknown")
        long_term_memories.append(
            LongTermMemoryItem(
                text=text,
                intent_label=label,
                timestamp=e.timestamp,
            )
        )

    # 3) 最近自省内容
    if reflection_path.exists():
        reflection_events = load_events_from_jsonl(reflection_path)
    else:
        reflection_events = []

    last_reflection: Optional[str] = None
    last_reflection_time: Optional[datetime] = None
    if reflection_events:
        last_event = max(reflection_events, key=lambda e: e.timestamp)
        payload = last_event.payload or {}
        last_reflection = str(payload.get("text") or "")
        last_reflection_time = last_event.timestamp

    # 4) 心境提示
    mood_hint = _compute_mood_hint(session_events)

    return WorkspaceState(
        recent_dialogue=recent_dialogue,
        long_term_memories=long_term_memories,
        last_reflection=last_reflection,
        last_reflection_time=last_reflection_time,
        mood_hint=mood_hint,
    )
