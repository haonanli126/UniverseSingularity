from __future__ import annotations

"""
对话记忆回放工具：

- 从 EmbryoEvent 列表中，提取出「用户 / 助手」对话消息
- 按时间顺序排列，并支持只取最近 N 条
"""

from typing import List, Literal, TypedDict

from .events import EmbryoEvent


class DialogueMessage(TypedDict):
    role: Literal["user", "assistant"]
    text: str


def events_to_dialogue(
    events: List[EmbryoEvent],
    max_messages: int | None = None,
) -> List[DialogueMessage]:
    """
    将事件列表转换为对话消息列表。

    规则：
    - 只保留 payload 中同时包含 role/text 的事件
    - role 只能是 "user" 或 "assistant"
    - 保持原有顺序（假设传入 events 已按时间排序）
    - 若 max_messages 不为 None，则只保留最后 max_messages 条
    """
    messages: List[DialogueMessage] = []

    for e in events:
        payload = e.payload or {}
        role = payload.get("role")
        text = payload.get("text")

        if not role or not text:
            continue

        if role not in {"user", "assistant"}:
            continue

        messages.append(DialogueMessage(role=role, text=str(text)))

    if max_messages is not None and max_messages > 0:
        messages = messages[-max_messages:]

    return messages
