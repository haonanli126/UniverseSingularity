from __future__ import annotations

"""
事件持久化工具：把 EmbryoEvent 按行写入 JSONL 文件，并支持读回。

- 每一行是一个 JSON，对应一个 EmbryoEvent
- 可用于简单的「会话日志 / 记忆回放」
"""

from pathlib import Path
from typing import List

from pydantic import ValidationError

from .events import EmbryoEvent


def append_event_to_jsonl(path: Path, event: EmbryoEvent) -> None:
    """
    追加写入一条事件到 JSONL 文件。

    Parameters
    ----------
    path : Path
        目标文件路径（若目录不存在会自动创建）。
    event : EmbryoEvent
        要写入的事件。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = event.model_dump_json()

    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_events_from_jsonl(path: Path) -> List[EmbryoEvent]:
    """
    从 JSONL 文件中读出所有事件。

    若文件不存在，返回空列表。
    若某一行损坏 / 解析失败，则跳过该行。
    """
    if not path.exists():
        return []

    events: List[EmbryoEvent] = []

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                event = EmbryoEvent.model_validate_json(line)
            except ValidationError:
                # 简单跳过坏行，避免整个加载失败
                continue
            events.append(event)

    return events
