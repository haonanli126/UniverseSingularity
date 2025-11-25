from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.neural.learning import ReplayBuffer  # noqa: E402


def test_replay_buffer_add_and_len():
    buf = ReplayBuffer(capacity=10)
    for i in range(7):
        s = np.zeros(100, dtype=np.float32) + i
        ns = s + 1
        buf.add(s, action=i % 3, reward=float(i), next_state=ns, done=False)
    assert len(buf) == 7


def test_replay_buffer_sample_shapes():
    buf = ReplayBuffer(capacity=100)
    for i in range(50):
        s = np.random.randn(100).astype(np.float32)
        ns = np.random.randn(100).astype(np.float32)
        buf.add(s, action=i % 6, reward=float(i), next_state=ns, done=(i % 2 == 0))

    states, actions, rewards, next_states, dones = buf.sample(batch_size=16)
    assert states.shape == (16, 100)
    assert actions.shape == (16,)
    assert rewards.shape == (16,)
    assert next_states.shape == (16, 100)
    assert dones.shape == (16,)
