from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import requests


@dataclass
class ChatMessage:
    """简单的聊天消息结构，用于统一和外部模型的交互格式。"""

    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class ModelApiClient:
    """最小可用的大模型 API 客户端封装。

    设计要点：
    - 默认支持 OpenAI 兼容 /chat/completions 接口
    - tests 可以通过传入 `call_fn` 来完全替代真实 HTTP 调用
    """

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        call_fn: Optional[Callable[[str, List[Dict[str, Any]]], str]] = None,
    ) -> None:
        # 测试里会只传 model + call_fn
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._call_fn = call_fn

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat_completion(self, messages: List[ChatMessage] | List[Dict[str, Any]]) -> str:
        """调用一次 ChatCompletion 接口。

        - 如果提供了 call_fn（测试/注入模式），直接把原始 messages 传给它；
        - 否则按 OpenAI 兼容协议走 HTTP 调用。
        """

        # ① 测试 / 注入模式：使用外部提供的函数，保持 messages 原样传递
        if self._call_fn is not None:
            return self._call_fn(self.model, messages)  # type: ignore[arg-type]

        # ② 默认模式：真实 HTTP 调用（OpenAI 兼容协议）
        #    这里才需要把 ChatMessage 转成 dict；如果本来就是 dict，就直接用。
        payload_messages: List[Dict[str, Any]] = [
            m.to_dict() if hasattr(m, "to_dict") else m  # type: ignore[union-attr]
            for m in messages
        ]

        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
        }

        resp = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # 尝试按 OpenAI 标准格式解析
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            # 兜底：如果服务端返回的是其他结构/字符串，避免直接崩掉
            if isinstance(data, str):
                return data
            return str(data)
