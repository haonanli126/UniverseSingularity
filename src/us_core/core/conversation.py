from __future__ import annotations

"""
对话引擎 v0（Phase 1 - S01）：

职责：
1. 从 JSONL 日志中读取历史 EmbryoEvent
2. 抽取出「user / assistant」对话消息
3. 基于最近 N 条对话 + 当前用户输入，构造给模型的 messages
4. 提供统一的「记录交互」方法，把本轮 user / assistant 事件写回 JSONL

注意：
- 这个模块本身不调用 OpenAI，只负责「上下文构造 + 事件记录」。
- 调用模型的部分由上层脚本（如 dialog_cli.py）完成。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .events import EmbryoEvent, EventType
from .persistence import append_event_to_jsonl, load_events_from_jsonl
from .recall import events_to_dialogue
from .intent import classify_intent


@dataclass
class ConversationEngineConfig:
    session_log_path: Path
    max_history_messages: int = 8  # 默认带入最近 8 条消息作为上下文


class ConversationEngine:
    def __init__(self, config: ConversationEngineConfig) -> None:
        self.config = config

    # ---------- 上下文构造 ----------

    def build_context_messages(self, user_text: str) -> List[Dict[str, str]]:
        """
        基于现有会话日志 + 当前用户输入，构造给模型的 messages 列表。

        messages 结构示例（不含 system 提示）：
        [
            {"role": "user", "content": "之前你说..."},
            {"role": "assistant", "content": "是的，我当时提到..."},
            ...
            {"role": "user", "content": "这是本轮最新的提问"}
        ]
        """
        events = load_events_from_jsonl(self.config.session_log_path)
        history_dialogue = events_to_dialogue(
            events, max_messages=self.config.max_history_messages
        )

        messages: List[Dict[str, str]] = []

        # 历史对话
        for m in history_dialogue:
            messages.append({"role": m["role"], "content": m["text"]})

        # 当前这一轮用户输入
        messages.append({"role": "user", "content": user_text})

        return messages

    # ---------- 事件记录 ----------

    def record_interaction(
            self,
            user_text: str,
            assistant_text: str,
    ) -> None:
        """
        把本轮 user / assistant 的发言记录为 EmbryoEvent，并写入 JSONL。

        同时对用户输入做一次简单意图识别，写入 payload.intent：
        {
            "label": "...",
            "confidence": 0.xx,
            "reason": "..."
        }
        """
        intent = classify_intent(user_text)

        # 用户输入事件
        user_event = EmbryoEvent(
            type=EventType.PERCEPTION,
            payload={
                "role": "user",
                "text": user_text,
                "intent": {
                    "label": intent.label.value,
                    "confidence": intent.confidence,
                    "reason": intent.reason,
                },
            },
        )
        append_event_to_jsonl(self.config.session_log_path, user_event)

        # 模型回复事件
        assistant_event = EmbryoEvent(
            type=EventType.SYSTEM,
            payload={
                "role": "assistant",
                "text": assistant_text,
            },
        )
        append_event_to_jsonl(self.config.session_log_path, assistant_event)

