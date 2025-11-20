from __future__ import annotations

"""
测试 Journal 模块（Phase 3 - S01 + S02）
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.journal import (
    JournalEntry,
    load_journal_entries_from_folder,
    journal_entry_to_event,
    extract_journal_snippets_from_events,
)


def test_load_journal_entries_from_folder_basic(tmp_path):
    folder = tmp_path / "journal"
    folder.mkdir()
    file_path = folder / "2025-01-01_hello.txt"
    file_path.write_text("今天有点累，但还可以。\n这是第二行。", encoding="utf-8")

    entries = load_journal_entries_from_folder(folder)
    assert len(entries) == 1

    entry = entries[0]
    # 时间戳类型正确即可（具体值由解析/mtime 决定）
    assert isinstance(entry.timestamp, datetime)
    assert entry.title == "今天有点累，但还可以。"
    assert "这是第二行" in entry.content
    assert entry.source_file == file_path


def test_journal_entry_to_event_basic():
    entry = JournalEntry(
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        title="测试日记",
        content="这是一段测试日记内容。",
        source_file=Path("dummy.txt"),
    )

    event = journal_entry_to_event(entry)
    assert isinstance(event, EmbryoEvent)
    assert event.type == EventType.MEMORY

    payload = event.payload or {}
    assert payload["kind"] == "journal_entry"
    assert payload["title"] == "测试日记"
    assert "测试日记内容" in payload["text"]
    assert payload["source_file"] == "dummy.txt"


def test_extract_journal_snippets_from_events_limit_and_order():
    now = datetime.now(timezone.utc)

    ev1 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=20),
        payload={"kind": "journal_entry", "title": "第一天，还挺累的。"},
    )
    ev2 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now - timedelta(seconds=10),
        payload={"kind": "journal_entry", "title": "第二天，心情好一点。"},
    )
    ev3 = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={"kind": "journal_entry", "title": "第三天，开始有点期待。"},
    )
    other = EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=now,
        payload={"kind": "note", "title": "不是日记"},
    )

    snippets = extract_journal_snippets_from_events([ev1, ev3, other, ev2], limit=2)
    # 应该只保留最近的两条 journal_entry（第二天 + 第三天）
    assert len(snippets) == 2
    assert "第二天" in snippets[0]
    assert "第三天" in snippets[1]
