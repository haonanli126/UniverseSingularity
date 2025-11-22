from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .channels import InputChannel
from .events import PerceptionEvent, PerceptionStore
from .emotion import estimate_emotion


def log_dialog_turn(
    conversation_id: str,
    turn_index: int,
    user_text: Optional[str],
    assistant_text: Optional[str],
    *,
    base_dir: Optional[str | Path] = None,
) -> Tuple[Optional[PerceptionEvent], Optional[PerceptionEvent]]:
    """
    记录一次对话轮次（user + assistant），并返回对应的感知事件。

    设计要点：
    - user_text / assistant_text 为空或全是空白时会被跳过，返回 None。
    - base_dir 不传时使用 PerceptionStore 的默认目录（data/perception）。
    - 每条事件都会带上 conversation_id / turn_index / role / emotion 信息。
    """
    store = PerceptionStore(base_dir=base_dir)

    user_event: Optional[PerceptionEvent] = None
    assistant_event: Optional[PerceptionEvent] = None

    if user_text and user_text.strip():
        emo = estimate_emotion(user_text)
        user_event = PerceptionEvent.create(
            channel=InputChannel.DIALOG,
            content=user_text,
            tags=["dialog", "user"],
            metadata={
                "role": "user",
                "conversation_id": conversation_id,
                "turn_index": turn_index,
                "emotion": emo.to_dict(),
                "source": "dialog_cli",
            },
        )
        store.append(user_event)

    if assistant_text and assistant_text.strip():
        emo = estimate_emotion(assistant_text)
        assistant_event = PerceptionEvent.create(
            channel=InputChannel.DIALOG,
            content=assistant_text,
            tags=["dialog", "assistant"],
            metadata={
                "role": "assistant",
                "conversation_id": conversation_id,
                "turn_index": turn_index,
                "emotion": emo.to_dict(),
                "source": "dialog_cli",
            },
        )
        store.append(assistant_event)

    return user_event, assistant_event
