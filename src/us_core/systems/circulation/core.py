from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .buffers import PerceptionBuffer, ActionQueue, MessageBus
from .api_client import ModelApiClient, ChatMessage


@dataclass
class CirculationSystem:
    """循环系统核心。

    管理：
    - 感官输入缓冲区
    - 运动输出队列
    - 内部消息总线
    - 外部大模型客户端（可选）
    """

    perception_buffer: PerceptionBuffer = field(default_factory=PerceptionBuffer)
    action_queue: ActionQueue = field(default_factory=ActionQueue)
    message_bus: MessageBus = field(default_factory=MessageBus)
    model_client: Optional[ModelApiClient] = None

    # ========= 感官相关 =========

    def ingest_perception(self, perception: Dict[str, Any]) -> None:
        """接收一条感知事件，放入缓冲区，并在总线上广播。"""
        self.perception_buffer.push(perception)
        self.message_bus.publish("perception", perception)

    def drain_perceptions(self) -> List[Dict[str, Any]]:
        """取出并清空感知缓冲区。"""
        return self.perception_buffer.pop_all()

    # ========= 动作相关 =========

    def queue_action(
        self,
        action: Dict[str, Any],
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """将动作放入优先级队列，并在消息总线上广播。"""
        self.action_queue.push(action, priority=priority, metadata=metadata or {})
        self.message_bus.publish("action_queued", {"action": action, "priority": priority})

    def get_actions_to_execute(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """按优先级依次取出待执行动作。"""
        results: List[Dict[str, Any]] = []
        while len(self.action_queue) > 0 and (limit is None or len(results) < limit):
            popped = self.action_queue.pop_next()
            if popped is None:
                break
            action, _meta = popped
            results.append(action)
        return results

    # ========= 消息广播 =========

    def broadcast(self, topic: str, payload: Dict[str, Any]) -> None:
        """向任意 topic 广播消息。"""
        self.message_bus.publish(topic, payload)

    # ========= 外部模型调用 =========

    def ask_model(self, messages: List[ChatMessage]) -> Optional[str]:
        """通过外部大模型客户端进行一次对话补全。

        如果尚未配置 model_client，则返回 None。
        """
        if self.model_client is None:
            return None
        return self.model_client.chat_completion(messages)
