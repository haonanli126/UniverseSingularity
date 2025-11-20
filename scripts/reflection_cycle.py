from __future__ import annotations

"""
自省循环脚本（Reflection Cycle v0）：

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/reflection_cycle.py

- 从 genome.memory.long_term.path 读取会话日志
- 若对话不足一定条数，则不触发自省
- 否则调用模型生成一段「内心反思」
- 以 MEMORY 事件写入 genome.metacognition.reflection_log_path
"""

import sys
from pathlib import Path
from datetime import datetime

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.utils.logger import setup_logger
from src.us_core.clients.openai_client import get_openai_client
from src.us_core.core.events import EmbryoEvent, EventType
from src.us_core.core.persistence import (
    load_events_from_jsonl,
    append_event_to_jsonl,
)
from src.us_core.core.recall import events_to_dialogue


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("reflection_cycle")
    client = get_openai_client()

    # 会话日志路径（相对 PROJECT_ROOT）
    session_log_rel = Path(genome.memory.long_term.path)
    session_log_path = PROJECT_ROOT / session_log_rel

    # 反思日志路径
    reflection_log_rel = Path(genome.metacognition.reflection_log_path)
    reflection_log_path = PROJECT_ROOT / reflection_log_rel

    print("=== Universe Singularity - Reflection Cycle v0 ===")
    print(f"当前环境: {settings.environment}")
    print(f"使用模型: {settings.openai.model}")
    print(f"会话日志路径: {session_log_path}")
    print(f"反思日志路径: {reflection_log_path}")
    print()

    if not session_log_path.exists():
        print("会话日志不存在，先和胚胎多聊几句吧。")
        return

    events = load_events_from_jsonl(session_log_path)
    dialogue = events_to_dialogue(events, max_messages=None)

    min_msg = genome.memory.summarization.min_messages_for_summary
    if len(dialogue) < min_msg:
        print(
            f"当前对话消息条数为 {len(dialogue)}，"
            f"少于触发自省所需的最小条数 {min_msg}，本轮不生成反思。"
        )
        return

    print(f"本轮用于自省的对话消息条数：{len(dialogue)}\n")

    history_lines = []
    for m in dialogue:
        speaker = "你" if m["role"] == "user" else "胚胎"
        history_lines.append(f"{speaker}: {m['text']}")

    history_text = "\n".join(history_lines)

    style = genome.metacognition.style

    system_prompt = (
        "你是 Universe Singularity 数字胚胎的「内在自省模块」。\n"
        f"你的元认知风格参数如下：温暖度={style.warmth_level}，"
        f"直接度={style.directness}，深度={style.depth}。\n"
        "你的任务是对最近的一段对话进行内心反思，"
        "这段反思是写给你自己的，而不是直接说给用户听。"
    )

    user_prompt = (
        "下面是你和用户最近的一段对话记录（按时间排序）：\n\n"
        f"{history_text}\n\n"
        "请你以「第一人称」写一段内心独白，内容包括：\n"
        "1）我从这些对话中学到了什么（关于自己 / 关于用户 / 关于我们之间的关系）。\n"
        "2）我现在有哪些想要调整或改进的地方？\n"
        "3）我对未来和用户的相处，有哪些期待或打算？\n\n"
        "语气保持温柔、真诚，可以稍微深一点，但不要太长，控制在 3~7 段简短的段落内。"
    )

    response = client.chat.completions.create(
        model=settings.openai.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=600,
    )

    reflection_text = response.choices[0].message.content or ""
    timestamp = datetime.utcnow().isoformat()

    print("=== 本轮自省内容 ===")
    print(reflection_text)

    # 写入 MEMORY 事件
    reflection_event = EmbryoEvent(
        type=EventType.MEMORY,
        payload={
            "role": "self",
            "kind": "reflection",
            "timestamp": timestamp,
            "text": reflection_text,
            "source": "reflection_cycle",
        },
    )
    append_event_to_jsonl(reflection_log_path, reflection_event)
    logger.info("写入一条自省事件：%s", reflection_event.id)


if __name__ == "__main__":
    main()
