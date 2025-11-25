from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, DefaultDict, Dict, List, Optional, Tuple
import heapq


@dataclass
class PerceptionBuffer:
    """感官输入缓冲区（FIFO）。

    设计目标：
    - 顺序保存最近的一批感知事件
    - 支持一次性取出（并清空）用于批处理
    """

    maxlen: int = 1024
    _buffer: Deque[Any] = field(init=False)

    def __post_init__(self) -> None:
        self._buffer = deque(maxlen=self.maxlen)

    def push(self, item: Any) -> None:
        self._buffer.append(item)

    def pop_all(self) -> List[Any]:
        items = list(self._buffer)
        self._buffer.clear()
        return items

    def __len__(self) -> int:  # pragma: no cover - 小函数
        return len(self._buffer)


@dataclass(order=True)
class _QueuedAction:
    """内部使用的动作元素（基于 heapq）。"""

    priority: int
    index: int
    action: Any = field(compare=False)
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False)


@dataclass
class ActionQueue:
    """运动输出缓冲区（优先级队列）。

    - priority 越小，优先级越高
    - index 保证 FIFO 语义（同优先级按入队顺序）
    """

    _heap: List[_QueuedAction] = field(default_factory=list, init=False)
    _counter: int = field(default=0, init=False)

    def push(self, action: Any, priority: int = 0, metadata: Optional[Dict[str, Any]] = None) -> None:
        if metadata is None:
            metadata = {}
        item = _QueuedAction(priority=priority, index=self._counter, action=action, metadata=metadata)
        self._counter += 1
        heapq.heappush(self._heap, item)

    def pop_next(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        if not self._heap:
            return None
        item = heapq.heappop(self._heap)
        return item.action, item.metadata

    def __len__(self) -> int:  # pragma: no cover
        return len(self._heap)


@dataclass
class MessageBus:
    """内部消息总线（发布-订阅风格的消息队列）。

    简化版本：
    - 按 topic 存放消息列表
    - 任何组件可以 publish(topic, message)
    - 消费者通过 get_messages(topic) 取出并（可选）清空
    """

    _topics: DefaultDict[str, List[Any]] = field(
        default_factory=lambda: defaultdict(list), init=False
    )

    def publish(self, topic: str, message: Any) -> None:
        self._topics[topic].append(message)

    def get_messages(self, topic: str, clear: bool = True) -> List[Any]:
        msgs = list(self._topics.get(topic, []))
        if clear and topic in self._topics:
            self._topics[topic].clear()
        return msgs

    def topics(self) -> List[str]:  # pragma: no cover - 用于调试
        return list(self._topics.keys())
