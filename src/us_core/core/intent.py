from __future__ import annotations

"""
简单规则版意图识别（Intent Tagging v0）：

目标：
- 不依赖模型，纯规则，快速给每句用户输入打一个标签
- 后续可用于：
  - 过滤长期记忆
  - 调整回复风格
  - 统计用户主要在聊什么
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class IntentLabel(str, Enum):
    CHAT = "chat"            # 普通聊天、陪伴
    PROJECT = "project"      # 关于「宇宙奇点 / 数字胚胎 / 项目」的内容
    EMOTION = "emotion"      # 情绪表达（难过、开心、焦虑等）
    COMMAND = "command"      # 明确让对方「帮忙做事」或执行任务
    META = "meta"            # 关于「我们关系 / 记忆 / 自身状态」的讨论
    UNKNOWN = "unknown"      # 无法判断 / 太短


@dataclass
class UtteranceIntent:
    label: IntentLabel
    confidence: float
    reason: str


def classify_intent(text: str) -> UtteranceIntent:
    """
    规则非常简单，后续可以逐步演化 / 接入模型。

    当前策略（从上到下匹配，遇到第一个强特征就返回）：
    - 情绪相关词汇 -> EMOTION
    - 明确的「帮我」「生成」「写一个」等 -> COMMAND
    - 项目 / Phase / 数字胚胎相关 -> PROJECT
    - 关于「我们关系 / 记忆 / 最近聊了什么」-> META
    - 否则 → CHAT
    """
    txt = text.strip()
    if not txt:
        return UtteranceIntent(
            label=IntentLabel.UNKNOWN,
            confidence=0.0,
            reason="空文本或仅空白字符",
        )

    lower = txt.lower()

    # 1) 情绪类关键词
    emotion_keywords = [
        "难过",
        "伤心",
        "开心",
        "孤单",
        "焦虑",
        "崩溃",
        "压力大",
        "委屈",
        "生气",
        "沮丧",
        "害怕",
    ]
    emotion_emojis = ["🥹", "😢", "😭", "😞", "😔", "😄", "😊", "😕"]
    if any(k in txt for k in emotion_keywords) or any(e in txt for e in emotion_emojis):
        return UtteranceIntent(
            label=IntentLabel.EMOTION,
            confidence=0.9,
            reason="命中情绪相关词汇或表情",
        )

    # 2) 明确的“帮我做事 / 生成 / 写”
    command_keywords = [
        "帮我",
        "生成",
        "写一个",
        "写段",
        "做一个",
        "实现",
        "写代码",
        "用python",
        "用 python",
        "给我一个脚本",
    ]
    if any(k in txt for k in command_keywords):
        return UtteranceIntent(
            label=IntentLabel.COMMAND,
            confidence=0.85,
            reason="命中指令 / 需求类关键词",
        )

    # 3) 项目 / Phase / 数字胚胎相关
    project_keywords = [
        "宇宙奇点",
        "universe singularity",
        "数字胚胎",
        "phase 0",
        "phase 1",
        "phase ",
        "对话 cli",
        "heartbeat",
        "reflection_cycle",
        "genome.yaml",
        "session_log.jsonl",
    ]
    if any(k.lower() in lower for k in project_keywords):
        return UtteranceIntent(
            label=IntentLabel.PROJECT,
            confidence=0.8,
            reason="命中项目 / Phase / 工程相关关键词",
        )

    # 4) 元话题：关于“我们”“记忆”“最近聊了什么”
    meta_patterns = [
        "我们最近在做什么",
        "你还记得",
        "你记得吗",
        "回顾一下",
        "总结一下",
        "你现在感觉怎么样",
        "你觉得自己现在",
    ]
    if any(p in txt for p in meta_patterns):
        return UtteranceIntent(
            label=IntentLabel.META,
            confidence=0.75,
            reason="命中元对话 / 关系相关表达",
        )

    # 5) 默认当作聊天
    return UtteranceIntent(
        label=IntentLabel.CHAT,
        confidence=0.6,
        reason="未命中特定模式，归类为普通聊天",
    )
