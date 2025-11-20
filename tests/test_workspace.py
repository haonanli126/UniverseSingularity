from __future__ import annotations

"""
测试全局工作空间快照构建逻辑。
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.persistence import append_event_to_jsonl
from src.us_core.core.workspace import (
    WorkspaceState,
    build_workspace_state,
)


def test_build_workspace_state_basic(tmp_path: Path):
    session_log = tmp_path / "session_log.jsonl"
    long_term_log = tmp_path / "long_term.jsonl"
    reflection_log = tmp_path / "reflections.jsonl"

    now = datetime.now(timezone.utc)

    # 会话事件：一轮简单对话
    user_event = EmbryoEvent(
        type=EventType.PERCEPTION,
        timestamp=now - timedelta(seconds=5),
        payload={
            "role": "user",
            "text": "我最近有点累",
            "intent": {
                "label": "emotion",
                "confidence": 0.9,
                "reason": "test",
            },
        },
    )
    assistant_event = EmbryoEvent(
        type=EventType.SYSTEM,
        timestamp=now - timedelta(seconds=4),
        payload={
            "role": "assistant",
            "text": "我在这里陪你。",
        },
    )
    append_event_to_jsonl(session_log, user_event)
    append_event_to_jsonl(session_log, assistant_event)

    # 长期记忆事件
    long_term_event = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=3),
        payload={
            "text": "我最近有点累",
            "intent": {
                "label": "emotion",
                "confidence": 0.9,
            },
        },
    )
    append_event_to_jsonl(long_term_log, long_term_event)

    # 自省事件
    reflection_event = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=1),
        payload={
            "text": "我意识到用户最近有些疲惫。",
        },
    )
    append_event_to_jsonl(reflection_log, reflection_event)

    ws: WorkspaceState = build_workspace_state(
        session_log_path=session_log,
        long_term_path=long_term_log,
        reflection_path=reflection_log,
        max_recent_messages=5,
        max_long_term=5,
    )

    assert isinstance(ws, WorkspaceState)
    assert len(ws.recent_dialogue) >= 2
    assert any(m.role == "user" for m in ws.recent_dialogue)
    assert len(ws.long_term_memories) == 1
    assert ws.last_reflection is not None
    assert ws.last_reflection_time is not None
    assert ws.mood_hint is not None


def test_build_workspace_state_empty(tmp_path: Path):
    session_log = tmp_path / "session_log.jsonl"
    long_term_log = tmp_path / "long_term.jsonl"
    reflection_log = tmp_path / "reflections.jsonl"

    ws: WorkspaceState = build_workspace_state(
        session_log_path=session_log,
        long_term_path=long_term_log,
        reflection_path=reflection_log,
    )

    assert ws.recent_dialogue == []
    assert ws.long_term_memories == []
    assert ws.last_reflection is None
    assert ws.last_reflection_time is None
    assert ws.mood_hint is None
