from __future__ import annotations

import json
import sys
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception.long_term_view import (
    load_memory_items_from_jsonl,
    build_daily_mood_from_memory_file,
)


def _write_records(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            json.dump(r, f, ensure_ascii=False)
            f.write("\n")


def test_load_memory_items_from_jsonl(tmp_path) -> None:
    path = tmp_path / "memory" / "perception_long_term.jsonl"
    records = [
        {
            "text": "今天很开心，也有点兴奋",
            "intent_label": "emotion",
            "timestamp": "2025-01-01T10:00:00+00:00",
        },
        {
            "text": "有点累，也有点焦虑",
            "intent_label": "emotion",
            "timestamp": "2025-01-01T22:00:00+00:00",
        },
    ]
    _write_records(path, records)

    items = load_memory_items_from_jsonl(path)
    assert len(items) == 2
    assert items[0].text.startswith("今天")
    assert items[0].intent_label == "emotion"


def test_build_daily_mood_from_memory_file(tmp_path) -> None:
    path = tmp_path / "memory" / "perception_long_term.jsonl"
    records = [
        {
            "text": "今天很开心，也有点兴奋",
            "intent_label": "emotion",
            "timestamp": "2025-01-01T10:00:00+00:00",
        },
        {
            "text": "有点累，也有点焦虑",
            "intent_label": "emotion",
            "timestamp": "2025-01-01T22:00:00+00:00",
        },
        {
            "text": "今天整体状态还可以，有一点期待",
            "intent_label": "emotion",
            "timestamp": "2025-01-02T09:00:00+00:00",
        },
    ]
    _write_records(path, records)

    daily = build_daily_mood_from_memory_file(path)
    assert len(daily) == 2

    days = {d.day.isoformat(): d for d in daily}
    assert "2025-01-01" in days
    assert "2025-01-02" in days

    # 2025-01-01 应该聚合了 2 条样本
    d1 = days["2025-01-01"]
    assert d1.sample_count == 2
