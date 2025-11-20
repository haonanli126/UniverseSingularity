from __future__ import annotations

"""
测试 ConversationEngine 的核心行为：

1. 在没有历史对话时，build_context_messages 只包含当前用户输入
2. 在有历史对话时，能：
   - 正确按顺序还原 user / assistant 消息
   - 正确截断为最近 N 条
3. record_interaction 能写入 JSONL，并可读回
"""

from pathlib import Path

from src.us_core.core.conversation import (
    ConversationEngine,
    ConversationEngineConfig,
)
from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.persistence import (
    append_event_to_jsonl,
    load_events_from_jsonl,
)


def test_build_context_messages_empty_history(tmp_path: Path):
    log_path = tmp_path / "session_log.jsonl"
    cfg = ConversationEngineConfig(session_log_path=log_path, max_history_messages=8)
    engine = ConversationEngine(cfg)

    messages = engine.build_context_messages("你好，测试一下。")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好，测试一下。"


def test_build_context_messages_with_history_and_limit(tmp_path: Path):
    log_path = tmp_path / "session_log.jsonl"

    # 构造一些历史事件：user / assistant 交替
    for i in range(1, 5):  # 4 轮对话 -> 共 8 条消息
        user_event = EmbryoEvent(
            type=EventType.PERCEPTION,
            payload={"role": "user", "text": f"user-{i}"},
        )
        assistant_event = EmbryoEvent(
            type=EventType.SYSTEM,
            payload={"role": "assistant", "text": f"assistant-{i}"},
        )
        append_event_to_jsonl(log_path, user_event)
        append_event_to_jsonl(log_path, assistant_event)

    cfg = ConversationEngineConfig(session_log_path=log_path, max_history_messages=3)
    engine = ConversationEngine(cfg)

    messages = engine.build_context_messages("new-question")

    # max_history_messages=3，意味着只保留最近 3 条历史消息 + 当前用户输入
    # 历史 full: [user-1, assistant-1, user-2, assistant-2, user-3, assistant-3, user-4, assistant-4]
    # 最近 3 条: [assistant-3, user-4, assistant-4]
    # 最终 messages: 上述 3 条 + 当前 user
    assert len(messages) == 4

    assert messages[0]["content"] == "assistant-3"
    assert messages[1]["content"] == "user-4"
    assert messages[2]["content"] == "assistant-4"
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == "new-question"


def test_record_interaction_writes_events(tmp_path: Path):
    log_path = tmp_path / "session_log.jsonl"
    cfg = ConversationEngineConfig(session_log_path=log_path, max_history_messages=5)
    engine = ConversationEngine(cfg)

    engine.record_interaction("你好", "我是胚胎")

    events = load_events_from_jsonl(log_path)
    assert len(events) == 2

    user_event, assistant_event = events

    assert user_event.payload["role"] == "user"
    assert user_event.payload["text"] == "你好"

    assert assistant_event.payload["role"] == "assistant"
    assert assistant_event.payload["text"] == "我是胚胎"
