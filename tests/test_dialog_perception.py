from __future__ import annotations

import sys
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import InputChannel, PerceptionStore, log_dialog_turn


def test_log_dialog_turn_creates_two_events(tmp_path) -> None:
    base_dir = tmp_path / "perception"
    conv_id = "conv-1"
    user_text = "今天有点累，但也挺期待的"
    assistant_text = "听起来有点累，但你保持期待很棒"

    user_event, assistant_event = log_dialog_turn(
        conversation_id=conv_id,
        turn_index=0,
        user_text=user_text,
        assistant_text=assistant_text,
        base_dir=base_dir,
    )

    assert user_event is not None
    assert assistant_event is not None

    store = PerceptionStore(base_dir=base_dir)
    events = list(store.iter_events())
    assert len(events) == 2

    u, a = events
    assert u.channel == InputChannel.DIALOG
    assert "dialog" in u.tags and "user" in u.tags
    assert u.metadata["role"] == "user"
    assert u.metadata["conversation_id"] == conv_id
    assert "emotion" in u.metadata
    assert isinstance(u.metadata["emotion"]["mood_score"], float)

    assert a.channel == InputChannel.DIALOG
    assert "dialog" in a.tags and "assistant" in a.tags
    assert a.metadata["role"] == "assistant"
    assert a.metadata["conversation_id"] == conv_id
    assert "emotion" in a.metadata


def test_log_dialog_turn_skips_empty_text(tmp_path) -> None:
    base_dir = tmp_path / "perception"
    conv_id = "conv-empty"

    user_event, assistant_event = log_dialog_turn(
        conversation_id=conv_id,
        turn_index=1,
        user_text="",
        assistant_text="",
        base_dir=base_dir,
    )

    assert user_event is None
    assert assistant_event is None

    store = PerceptionStore(base_dir=base_dir)
    events = list(store.iter_events())
    assert events == []
