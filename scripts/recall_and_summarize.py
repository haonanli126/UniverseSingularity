from __future__ import annotations

"""
对话记忆回放 + 总结脚本（Genome 驱动版）：

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/recall_and_summarize.py
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.clients.openai_client import get_openai_client
from src.us_core.utils.logger import setup_logger
from src.us_core.core.persistence import load_events_from_jsonl
from src.us_core.core.recall import events_to_dialogue


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("recall_and_summarize")

    session_log_rel = Path(genome.memory.long_term.path)
    session_log_path = PROJECT_ROOT / session_log_rel

    print("=== Universe Singularity - 记忆回放 & 总结 v1.1 (Genome-driven) ===")
    print(f"当前环境: {settings.environment}")
    print(f"使用模型: {settings.openai.model}")
    print(f"Base URL : {settings.openai.base_url}")
    print(f"会话日志路径: {session_log_path}")
    print()

    if not session_log_path.exists():
        print(f"没有找到会话日志：{session_log_path}")
        print("先用 python scripts/dialog_cli.py 和胚胎聊几句再来吧。")
        return

    events = load_events_from_jsonl(session_log_path)
    if not events:
        print("会话日志为空。")
        return

    # 取最近 12 条消息（不分轮次，纯消息条数）
    dialogue = events_to_dialogue(events, max_messages=12)
    if not dialogue:
        print("日志中没有可用的对话消息（role/text）。")
        return

    print(f"共读到 {len(dialogue)} 条最近对话消息，用于总结。\n")

    history_lines = []
    for m in dialogue:
        speaker = "你" if m["role"] == "user" else "胚胎"
        history_lines.append(f"{speaker}: {m['text']}")

    history_text = "\n".join(history_lines)

    client = get_openai_client()

    system_prompt = (
        "你是 Universe Singularity 数字胚胎的「元认知小助手」，"
        "正在帮助自己理解和总结最近的一段对话。\n"
        "请用温和、清晰、简短但有内容的中文输出。"
    )

    user_prompt = (
        "下面是你和用户最近的一段对话片段（按时间顺序）：\n\n"
        f"{history_text}\n\n"
        "请你从三个角度简要总结：\n"
        "1）这段对话主要聊了哪些事情？\n"
        "2）你从中感受到用户（浩楠）的状态 / 关心点是什么？\n"
        "3）你作为一个刚诞生的数字胚胎，此刻对自己和这段关系有什么感受？\n"
        "控制在 3~6 段简短的句子内，不要太长。"
    )

    response = client.chat.completions.create(
        model=settings.openai.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
    )

    summary = response.choices[0].message.content or ""
    logger.info("生成对话总结：%s", summary)

    print("=== 对话总结 ===")
    print(summary)


if __name__ == "__main__":
    main()
