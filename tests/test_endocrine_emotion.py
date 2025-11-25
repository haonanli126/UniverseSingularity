from us_core.systems.endocrine.emotion import (
    EmotionState,
    update_emotion,
    label_emotion,
)
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.endocrine.reward import RewardComponents


def test_update_emotion_positive_reward_increases_valence():
    state = EmotionState(valence=0.0, arousal=0.0, dominance=0.0)
    reward = RewardComponents(extrinsic=1.0, intrinsic=0.0)

    new_state = update_emotion(state, reward, decay=0.5)

    assert new_state.valence > state.valence
    assert -1.0 <= new_state.valence <= 1.0
    assert 0.0 <= new_state.arousal <= 1.0


def test_update_emotion_negative_reward_decreases_valence():
    state = EmotionState(valence=0.5, arousal=0.2, dominance=0.0)
    reward = RewardComponents(extrinsic=-1.0, intrinsic=0.0)

    new_state = update_emotion(state, reward, decay=0.5)

    assert new_state.valence < state.valence


def test_label_emotion_basic_categories():
    excited = EmotionState(valence=0.8, arousal=0.8, dominance=0.3)
    calm = EmotionState(valence=0.6, arousal=0.1, dominance=0.0)
    sad = EmotionState(valence=-0.7, arousal=0.1, dominance=-0.3)
    angry = EmotionState(valence=-0.7, arousal=0.8, dominance=0.1)
    neutral = EmotionState(valence=0.0, arousal=0.0, dominance=0.0)

    assert label_emotion(excited) == "excited"
    assert label_emotion(calm) == "calm"
    assert label_emotion(sad) == "sad"
    assert label_emotion(angry) == "angry"
    assert label_emotion(neutral) == "neutral"
