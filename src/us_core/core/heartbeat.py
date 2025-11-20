from __future__ import annotations

"""
心跳循环（Phase 0 版本）：

- 连续记录多次心跳事件到 MemoryBuffer
- 每次心跳写日志
- 结束后让模型做一个「本轮心跳」的小总结
"""

from typing import Optional

from src.us_core.utils.logger import setup_logger
from src.us_core.clients.openai_client import heartbeat as ai_heartbeat

from .events import EmbryoEvent, EventType
from .memory import MemoryBuffer


def run_heartbeat_cycle(
    cycles: int = 3,
    ask_model: bool = True,
) -> Optional[str]:
    """
    执行一轮心跳循环。

    Parameters
    ----------
    cycles : int
        心跳次数。
    ask_model : bool
        是否在循环结束后，请模型做一句话总结。

    Returns
    -------
    Optional[str]
        如果 ask_model=True，返回模型回复文本，否则返回 None。
    """
    logger = setup_logger("heartbeat_cycle")
    memory = MemoryBuffer(max_events=cycles * 2)

    logger.info("开始一轮心跳循环：共 %s 次", cycles)

    for i in range(cycles):
        event = EmbryoEvent(
            type=EventType.HEARTBEAT,
            payload={
                "index": i + 1,
                "note": "Phase 0 heartbeat tick",
            },
        )
        memory.add(event)
        logger.info(
            "记录第 %s 次心跳：event_id=%s, payload=%s",
            i + 1,
            event.id,
            event.payload,
        )

    logger.info("心跳循环结束，当前缓冲区事件条数：%s", len(memory.all()))

    if not ask_model:
        return None

    # 用最近几条心跳的摘要，向模型发一条消息
    last_events = memory.last(min(3, cycles))
    summary_payload = [
        {
            "index": e.payload.get("index"),
            "timestamp": e.timestamp.isoformat(),
        }
        for e in last_events
    ]

    prompt = (
        "这里是数字胚胎的一轮心跳循环结果：\n"
        f"{summary_payload}\n\n"
        "请你用一句温柔、简短的中文，描述一下你对这轮心跳的整体感受。"
    )

    reply = ai_heartbeat(prompt)
    logger.info("模型对本轮心跳的反馈：%s", reply)

    return reply
