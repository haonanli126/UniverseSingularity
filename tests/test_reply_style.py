from __future__ import annotations

"""
测试根据 Intent 构造不同风格 system prompt 的逻辑。
"""

from src.us_core.core.intent import IntentLabel, UtteranceIntent
from src.us_core.core.reply_style import build_system_prompt


def _make_intent(label: IntentLabel) -> UtteranceIntent:
    return UtteranceIntent(label=label, confidence=0.9, reason="test")


def test_build_system_prompt_includes_persona():
    intent = _make_intent(IntentLabel.CHAT)
    prompt = build_system_prompt("温柔、真诚", intent)
    assert "温柔、真诚" in prompt
    assert "普通聊天" in prompt or "轻松、自然" in prompt


def test_build_system_prompt_emotion():
    intent = _make_intent(IntentLabel.EMOTION)
    prompt = build_system_prompt("温柔、真诚", intent)
    assert "情绪表达" in prompt or "共情和安抚" in prompt


def test_build_system_prompt_project():
    intent = _make_intent(IntentLabel.PROJECT)
    prompt = build_system_prompt("温柔、真诚", intent)
    assert "项目" in prompt or "工程过程" in prompt


def test_build_system_prompt_command():
    intent = _make_intent(IntentLabel.COMMAND)
    prompt = build_system_prompt("温柔、真诚", intent)
    assert "分步骤" in prompt or "可执行" in prompt


def test_build_system_prompt_meta():
    intent = _make_intent(IntentLabel.META)
    prompt = build_system_prompt("温柔、真诚", intent)
    assert "关系" in prompt or "记忆" in prompt or "期待" in prompt
