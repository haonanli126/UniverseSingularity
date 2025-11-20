from __future__ import annotations

"""
测试简单规则版意图识别：
"""

from src.us_core.core.intent import (
    IntentLabel,
    classify_intent,
)


def test_classify_emotion():
    intent = classify_intent("我最近有点难过，压力也很大")
    assert intent.label == IntentLabel.EMOTION
    assert intent.confidence > 0.5


def test_classify_project():
    intent = classify_intent("我们下一步的 Universe Singularity Phase 1 做什么？")
    assert intent.label == IntentLabel.PROJECT


def test_classify_command():
    intent = classify_intent("帮我写一个 Python 脚本，读取 session_log.jsonl")
    assert intent.label == IntentLabel.COMMAND


def test_classify_meta():
    intent = classify_intent("你还记得我们昨天聊了什么吗？")
    assert intent.label == IntentLabel.META


def test_classify_default_chat():
    intent = classify_intent("今天天气怎么样，你会不会觉得无聊？")
    assert intent.label == IntentLabel.CHAT
