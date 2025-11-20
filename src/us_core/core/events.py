from __future__ import annotations

"""
核心事件模型：数字胚胎内部流动的「信号单位」。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict
import uuid

from pydantic import BaseModel, Field


class EventType(str, Enum):
    HEARTBEAT = "heartbeat"
    PERCEPTION = "perception"
    MEMORY = "memory"
    SYSTEM = "system"


class EmbryoEvent(BaseModel):
    """
    通用事件结构：

    - type: 事件类型（心跳 / 感知 / 记忆 / 系统）
    - timestamp: 创建时间（UTC）
    - payload: 自由扩展字段，后续所有系统都往这里塞数据
    """

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="事件唯一 ID",
    )
    type: EventType
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="事件创建时间（UTC）",
    )
    payload: Dict[str, Any] = Field(default_factory=dict)
