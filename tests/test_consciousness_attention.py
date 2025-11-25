import pytest

from us_core.systems.consciousness.attention import (
    AttentionFilter,
    AttentionAllocator,
    AttentionMonitor,
)


def test_attention_filter_removes_low_relevance():
    f = AttentionFilter(min_relevance=0.5)
    candidates = {"a": 0.2, "b": 0.5, "c": 0.8}

    filtered = f.filter(candidates)
    assert filtered == {"b": 0.5, "c": 0.8}


def test_attention_allocator_normalizes_weights():
    allocator = AttentionAllocator()
    weights = allocator.allocate({"a": 1.0, "b": 2.0})

    total = weights["a"] + weights["b"]
    assert pytest.approx(total, rel=1e-6) == 1.0
    assert weights["b"] > weights["a"]


def test_attention_monitor_keeps_bounded_history():
    monitor = AttentionMonitor(max_history=2)

    monitor.record({"a": 0.1})
    monitor.record({"b": 0.2})
    monitor.record({"c": 0.3})

    history = monitor.history
    assert len(history) == 2
    # 应该保留最近两次
    assert history[0].scores == {"b": 0.2}
    assert history[1].scores == {"c": 0.3}
