from __future__ import annotations

import sys
from pathlib import Path

# --- 确保可以从 src/ 下导入 us_core 包 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # D:/UniverseSingularity
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from us_core.perception import EmotionEstimate, estimate_emotion


def test_emotion_positive_text() -> None:
    text = "今天很开心，也有一点期待"
    emo = estimate_emotion(text)

    assert isinstance(emo, EmotionEstimate)
    assert emo.sentiment == "positive"
    assert emo.mood_score > 0
    assert "开心" in emo.keywords or "期待" in emo.keywords


def test_emotion_negative_text() -> None:
    text = "有点累，也有点焦虑"
    emo = estimate_emotion(text)

    assert emo.sentiment == "negative"
    assert emo.mood_score < 0
    assert any(w in emo.keywords for w in ["累", "焦虑"])


def test_emotion_empty_text_neutral() -> None:
    emo = estimate_emotion("")
    assert emo.sentiment == "neutral"
    assert emo.mood_score == 0.0
    assert emo.energy_level == 0.0
