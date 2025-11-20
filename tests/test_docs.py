from __future__ import annotations

from pathlib import Path


def test_readme_mentions_daily_cycle_and_mood():
    text = Path("README.md").read_text(encoding="utf-8")
    # 确保 README 至少提到了 daily_cycle 和 情绪感知 TODO
    assert "daily_cycle.py" in text
    assert "情绪感知 TODO" in text


def test_phase0_timeline_doc_exists():
    path = Path("docs/PHASE0_TIMELINE.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "Phase 0 时间线" in content
    assert "Universe Singularity" in content
