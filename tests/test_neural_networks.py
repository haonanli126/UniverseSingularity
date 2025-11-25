from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.systems.neural.networks import (  # noqa: E402
    FeatureExtractor,
    PolicyNetwork,
    ValueNetwork,
    WorldModel,
)


def test_policy_network_forward_shape_and_finiteness():
    net = PolicyNetwork(input_size=100, output_size=6)
    x = np.random.randn(1, 100).astype(np.float32)
    out = net.forward(x)
    assert out.shape == (1, 6)
    assert np.all(np.isfinite(out))


def test_value_network_forward_shape():
    net = ValueNetwork(input_size=100)
    x = np.random.randn(5, 100).astype(np.float32)
    out = net.forward(x)
    assert out.shape == (5, 1)


def test_feature_extractor_output_dim():
    fe = FeatureExtractor(input_size=100, feature_dim=32)
    x = np.random.randn(2, 100).astype(np.float32)
    out = fe.forward(x)
    assert out.shape == (2, 32)


def test_world_model_predict_next_state_shape():
    wm = WorldModel(state_dim=100, num_actions=6)
    state = np.random.randn(3, 100).astype(np.float32)
    next_state = wm.predict_next_state(state, action=2)
    assert next_state.shape == (3, 100)
