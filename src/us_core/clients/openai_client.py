"""
OpenAI 客户端封装（数字胚胎的「声带」）。

- 提供一个全局 OpenAI client（基于代理 Base URL）
- 提供一个 heartbeat() 函数，用来做最简单的连通性检测
"""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from config.settings import get_settings


@lru_cache
def get_openai_client() -> OpenAI:
    """
    获取一个全局复用的 OpenAI 客户端。
    """
    settings = get_settings()

    client = OpenAI(
        base_url=settings.openai.base_url,
        api_key=settings.openai.api_key,
        timeout=settings.openai.timeout,
    )
    return client


def heartbeat(message: str = "这里是数字胚胎心跳检测。") -> str:
    """
    发起一次最简单的 Chat Completion 请求，验证：
    - .env / 配置是否正确
    - 代理是否可用
    - 模型是否可用
    """
    settings = get_settings()
    client = get_openai_client()

    response = client.chat.completions.create(
        model=settings.openai.model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Universe Singularity 数字胚胎的核心系统。"
                    "用简短、友好的中文回应一条心跳消息。"
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        max_tokens=64,
    )

    return response.choices[0].message.content
