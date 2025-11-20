from __future__ import annotations

"""
Journal 模块（Phase 3 - S01 + S02）

作用：
- 定义 JournalEntry 数据结构
- 从 data/journal/ 文件夹加载 .txt 日记
- 把日记条目转换为 EmbryoEvent（kind = "journal_entry"）
- 从事件流中提取最近的日记片段摘要（用于 Workspace / 规划）
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .events import EmbryoEvent, EventType


@dataclass
class JournalEntry:
    """
    表示一条外部日记记录（来自本地 .txt 文件）：
    - timestamp: 这条日记对应的时间（可从首行解析，或者用文件修改时间兜底）
    - title: 日记标题（默认取首个非空行）
    - content: 文件全文内容
    - source_file: 源文件路径
    """

    timestamp: datetime
    title: str
    content: str
    source_file: Path


def _infer_timestamp(path: Path, first_non_empty: str | None) -> datetime:
    """
    尝试从首行解析时间；失败则使用文件 mtime，最后兜底为当前时间（UTC）。
    支持格式：
    - YYYY-MM-DD HH:MM:SS
    - YYYY-MM-DD HH:MM
    """
    if first_non_empty:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt_naive = datetime.strptime(first_non_empty, fmt)
                return dt_naive.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    try:
        stat = path.stat()
        return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    except OSError:
        return datetime.now(timezone.utc)


def load_journal_entries_from_folder(folder: Path, encoding: str = "utf-8") -> List[JournalEntry]:
    """
    从给定文件夹中加载所有 .txt 日记文件，按文件名排序。

    规则：
    - 标题：取文件内容中的首个非空行；如果文件全空，则用文件名（不含扩展名）
    - 时间戳：
        - 优先尝试用首个非空行解析（如果是时间字符串）
        - 否则使用文件修改时间 mtime
    """
    entries: List[JournalEntry] = []

    if not folder.exists():
        return entries

    for path in sorted(folder.glob("*.txt")):
        text = path.read_text(encoding=encoding)
        lines = [line.strip() for line in text.splitlines()]
        non_empty = [l for l in lines if l]

        title = non_empty[0] if non_empty else path.stem
        timestamp = _infer_timestamp(path, non_empty[0] if non_empty else None)

        entries.append(
            JournalEntry(
                timestamp=timestamp,
                title=title,
                content=text,
                source_file=path,
            )
        )

    return entries


def journal_entry_to_event(entry: JournalEntry) -> EmbryoEvent:
    """
    把一条 JournalEntry 转换为 EmbryoEvent：
    - type: MEMORY
    - payload.kind: "journal_entry"
    """
    return EmbryoEvent(
        type=EventType.MEMORY,
        timestamp=entry.timestamp,
        payload={
            "kind": "journal_entry",
            "title": entry.title,
            "text": entry.content,
            "source_file": str(entry.source_file),
        },
    )


def extract_journal_snippets_from_events(
    events: Iterable[EmbryoEvent],
    limit: int = 3,
    max_len: int = 80,
) -> List[str]:
    """
    从一批事件中提取最近的若干「日记片段摘要」，按时间排序后取最后 limit 条。

    优先使用 payload.title 作为摘要，否则使用 text 的前若干字符。
    """
    candidates: List[tuple[datetime, str]] = []

    for e in events:
        if e.type is not EventType.MEMORY:
            continue
        payload = e.payload or {}
        if payload.get("kind") != "journal_entry":
            continue

        ts = e.timestamp
        title = str(payload.get("title") or "").strip()
        text = str(payload.get("text") or "").strip()

        base = title if title else text
        if not base:
            continue

        if len(base) > max_len:
            base = base[: max_len - 3] + "..."

        candidates.append((ts, base))

    # 按时间排序，取最近的 limit 条
    candidates.sort(key=lambda x: x[0])
    snippets = [s for _, s in candidates[-limit:]]
    return snippets
