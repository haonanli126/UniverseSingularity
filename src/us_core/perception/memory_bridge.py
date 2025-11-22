from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .channels import InputChannel
from .emotion import estimate_emotion, EmotionEstimate
from .events import PerceptionEvent, PerceptionStore
from ..core.workspace import LongTermMemoryItem  # us_core.core.workspace


@dataclass
class MemoryBridgeConfig:
    """
    感知 → 长期记忆 的简单规则配置。

    目前是硬编码规则，后面可以接 genome / YAML 配置。
    """

    # 情绪强度阈值（|mood_score| >= 这个值时认为值得进入记忆）
    # 这里取 0.05：像「有点累，但也挺期待」这种轻微但真实的心情也会被记住。
    min_abs_mood_for_dialog: float = 0.05


DEFAULT_CONFIG = MemoryBridgeConfig()


def _is_obvious_noise(text: str) -> bool:
    """
    过滤非常明显的命令行噪音/控制指令，避免「cd / pytest / q」被写入长期记忆。
    """
    if not text:
        return True

    t = text.strip()

    if t in {"q", ":q", "exit", "quit", ":quit"}:
        return True

    lower = t.lower()
    if lower.startswith(("cd ", "dir ", "ls ", "pytest ", "python ")):
        return True
    if lower.startswith(("get-content", "cat ", "echo ")):
        return True

    # 粗略判断一下 Windows 路径 / 脚本调用
    if ":\\\\" in t or t.startswith(".\\") or t.startswith("./"):
        return True

    return False


def _classify_intent_for_event(
    event: PerceptionEvent,
    emotion: EmotionEstimate,
    *,
    cfg: MemoryBridgeConfig,
) -> Optional[str]:
    """
    根据事件的渠道 / tags / 情绪估计，给出一个 intent_label。

    返回：
      - "emotion" / "note" / ... 具体 label
      - None 表示不写入长期记忆
    """
    text = (event.content or "").strip()
    if not text:
        return None

    # 1）心情打卡 -> emotion（但过滤明显噪音）
    if event.channel is InputChannel.CLI_CHECKIN:
        if _is_obvious_noise(text):
            return None
        return "emotion"

    # 2）速记 -> note（即便没情绪，也可能是重要 idea）
    if event.channel is InputChannel.CLI_NOTE:
        if _is_obvious_noise(text):
            return None
        return "note"

    # 3）对话 -> 只考虑 user 说的话，且情绪比较明显时记为 emotion
    if event.channel is InputChannel.DIALOG:
        role = (event.metadata or {}).get("role")
        if role != "user":
            return None

        if abs(emotion.mood_score) >= cfg.min_abs_mood_for_dialog:
            return "emotion"
        # 情绪太弱就先不写入长期记忆
        return None

    # 其它渠道暂时忽略
    return None


def perception_event_to_memory_item(
    event: PerceptionEvent,
    *,
    cfg: MemoryBridgeConfig = DEFAULT_CONFIG,
) -> Optional[LongTermMemoryItem]:
    """
    把单条感知事件转换为 LongTermMemoryItem（如果规则认为值得记）。

    规则：
      - CLI_CHECKIN：过滤掉命令噪音后，统一记为 intent="emotion"
      - CLI_NOTE：过滤掉命令噪音后，统一记为 intent="note"
      - DIALOG：只记录 role=user 且情绪强度超过阈值的句子，intent="emotion"
      - 其余情况返回 None
    """
    text = (event.content or "").strip()
    if not text:
        return None

    # 统一再算一次情绪，这样即使 metadata 里没有 emotion 也能工作
    emotion = estimate_emotion(text)
    intent = _classify_intent_for_event(event, emotion, cfg=cfg)
    if intent is None:
        return None

    return LongTermMemoryItem(
        text=text,
        intent_label=intent,
        timestamp=event.timestamp,
    )


def build_memory_items_from_perception(
    events: Iterable[PerceptionEvent],
    *,
    cfg: MemoryBridgeConfig = DEFAULT_CONFIG,
) -> List[LongTermMemoryItem]:
    """
    批量把感知事件转换为 LongTermMemoryItem 列表。

    只返回被规则选中的事件对应的条目，顺序与输入事件顺序一致。
    """
    items: List[LongTermMemoryItem] = []
    for ev in events:
        item = perception_event_to_memory_item(ev, cfg=cfg)
        if item is not None:
            items.append(item)
    return items


def ingest_perception_events_to_file(
    store: PerceptionStore,
    *,
    output_path: str | Path,
    channel: InputChannel | None = None,
    limit: int | None = None,
    cfg: MemoryBridgeConfig = DEFAULT_CONFIG,
) -> List[LongTermMemoryItem]:
    """
    从 PerceptionStore 中读取事件，应用桥接规则，写入 JSONL 文件作为长期记忆的一部分。

    - output_path: 目标 JSONL 文件路径（会以追加模式写入）
    - channel: 可选，只处理某个渠道（cli_checkin / dialog / ...），None 为全部
    - limit: 可选，最多读取多少条（按时间顺序）。None 表示不限制。
    - 返回：本次实际写入的 LongTermMemoryItem 列表

    注意：不做去重，多次对同一批事件执行可能产生重复记录。
    """
    # 从感知仓库中取出事件
    events_iter = store.iter_events(channel=channel, limit=limit, reverse=False)
    events = list(events_iter)

    items = build_memory_items_from_perception(events, cfg=cfg)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        for item in items:
            record = {
                "text": item.text,
                "intent_label": item.intent_label,
                "timestamp": item.timestamp.isoformat(),
            }
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    return items
