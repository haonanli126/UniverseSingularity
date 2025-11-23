from pathlib import Path
import sys
import json

# 确保 src 在 sys.path 里
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.planner.mode_resolver import resolve_mode_from_mood_files  # type: ignore


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_resolve_mode_from_explicit_mode_key(tmp_path: Path):
    mood_file = tmp_path / "data" / "mood" / "today_mood.json"
    _write_json(mood_file, {"mode": "rest"})

    info = resolve_mode_from_mood_files(base_dir=tmp_path)
    assert info.mode == "rest"
    assert "today_mood.json" in info.source


def test_resolve_mode_from_dominant_mood(tmp_path: Path):
    mood_file = tmp_path / "data" / "mood" / "today_mood.json"
    _write_json(mood_file, {"dominant_mood": "excited"})

    info = resolve_mode_from_mood_files(base_dir=tmp_path)
    # excited → focus
    assert info.mode == "focus"


def test_resolve_mode_falls_back_to_preferred_mode_when_no_files(tmp_path: Path):
    info = resolve_mode_from_mood_files(base_dir=tmp_path, preferred_mode="rest")
    assert info.mode == "rest"
    assert info.source == "fallback"


def test_resolve_mode_falls_back_to_balance_when_no_preferred(tmp_path: Path):
    info = resolve_mode_from_mood_files(base_dir=tmp_path)
    assert info.mode == "balance"
    assert info.source == "fallback"
