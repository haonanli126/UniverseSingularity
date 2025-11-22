from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from .channels import InputChannel


def _default_root_dir() -> Path:
    """
    从当前文件位置推断项目根目录（git 仓库根）。

    目前假设当前文件路径类似：
        <root>/src/us_core/perception/events.py

    Path(__file__).resolve().parents 的含义：
        [0] = events.py
        [1] = perception
        [2] = us_core
        [3] = src
        [4] = <root>

    所以这里取 parents[4] 作为仓库根目录。
    """
    try:
        return Path(__file__).resolve().parents[4]
    except Exception:
        return Path.cwd()



def _default_base_dir() -> Path:
    """
    默认的感知存储目录：

      1）如果设置了环境变量 US_PERCEPTION_DIR，就用那一个；
      2）否则使用 <root>/data/perception
    """
    env_dir = os.getenv("US_PERCEPTION_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    return _default_root_dir() / "data" / "perception"


@dataclass
class PerceptionEvent:
    """
    数字胚胎对世界的一次“感知”。

    Phase 1 先聚焦文本输入（命令行速记 / 心情打卡 / 对话 / 日记），
    但结构设计为通用格式，后面可以挂更多模态（例如标签、情绪、向量等）。
    """

    id: str
    timestamp: datetime
    channel: InputChannel
    content: str
    tags: List[str]
    metadata: Dict[str, Any]

    @classmethod
    def create(
        cls,
        channel: InputChannel,
        content: str,
        *,
        tags: Optional[Iterable[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> "PerceptionEvent":
        """统一入口，带默认值。"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}

        return cls(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            channel=channel,
            content=content,
            tags=list(tags),
            metadata=dict(metadata),
        )

    def to_dict(self) -> Dict[str, Any]:
        """用于 JSONL 存储的 dict 形式。"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["channel"] = self.channel.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerceptionEvent":
        """从 JSON/dict 恢复为 PerceptionEvent。"""
        timestamp_raw = data.get("timestamp")
        if isinstance(timestamp_raw, str):
            timestamp = datetime.fromisoformat(timestamp_raw)
        elif isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw
        else:
            # 如果缺失就当作“现在”，避免因为历史数据脏而崩掉
            timestamp = datetime.now(timezone.utc)

        channel_raw = data.get("channel", InputChannel.SYSTEM.value)
        try:
            channel = InputChannel(channel_raw)
        except ValueError:
            channel = InputChannel.SYSTEM

        return cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            timestamp=timestamp,
            channel=channel,
            content=str(data.get("content", "")),
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
        )


class PerceptionStore:
    """
    感知事件的简单持久化层（JSONL 形式，追加写入）。

    设计思路：
    - Phase 1 保持朴素实现（单文件 append），逻辑足够清晰
    - 未来 Phase 2/3 想换成 SQLite / 向量库 / 专门的时间序列存储都可以用同样接口替换
    """

    def __init__(self, base_dir: Optional[Path | str] = None) -> None:
        if base_dir is None:
            base_dir = _default_base_dir()
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)

        self.base_dir: Path = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._events_file: Path = self.base_dir / "events.jsonl"

    @property
    def events_file(self) -> Path:
        return self._events_file

    def append(self, event: PerceptionEvent) -> None:
        """在 JSONL 文件末尾追加一条事件。"""
        record = event.to_dict()
        with self._events_file.open("a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    def iter_events(
        self,
        *,
        channel: Optional[InputChannel] = None,
        limit: Optional[int] = None,
        reverse: bool = False,
    ) -> Iterator[PerceptionEvent]:
        """
        遍历事件，可按渠道过滤，并限制数量。

        reverse=True 时会先把行反转，相当于从最新往前看。
        （当前实现会全文件读入到内存，后续可优化成流式 / 索引查询。）
        """
        if not self._events_file.exists():
            return iter(())

        with self._events_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        if reverse:
            lines = list(reversed(lines))

        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                event = PerceptionEvent.from_dict(raw)
            except Exception:
                # 忽略坏行，避免因为某次写坏数据导致整体瘫痪
                continue

            if channel is not None and event.channel is not channel:
                continue

            yield event
            count += 1
            if limit is not None and count >= limit:
                break

    def latest(
        self,
        *,
        channel: Optional[InputChannel] = None,
        limit: int = 10,
    ) -> List[PerceptionEvent]:
        """返回最新的 N 条事件（按追加顺序）。"""
        return list(self.iter_events(channel=channel, limit=limit, reverse=True))
