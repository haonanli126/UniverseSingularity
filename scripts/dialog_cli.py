from __future__ import annotations

"""
对话 CLI v1.1（Genome 驱动版）：

- 使用 ConversationEngine 读取最近对话上下文
- 会话日志路径 & 历史长度，从 genome.yaml 中读取
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
from src.us_core.utils.logger import setup_logger
from src.us_core.clients.openai_client import get_openai_client
from src.us_core.core.conversation import ConversationEngine, ConversationEngineConfig
from src.us_core.core.intent import classify_intent
from src.us_core.core.reply_style import build_system_prompt



def main() -> None:
    settings = get_settings()
    genome = get_genome()

    logger = setup_logger("dialog_cli")
    client = get_openai_client()

    # 会话日志路径：从 genome.memory.long_term.path 读取（相对 PROJECT_ROOT）
    session_log_rel = Path(genome.memory.long_term.path)
    session_log_path = PROJECT_ROOT / session_log_rel

    # 历史长度：从 genome.conversation.history.max_messages 读取，默认 8
    if genome.conversation is not None:
        max_history = genome.conversation.history.max_messages
    else:
        max_history = 8

    engine_cfg = ConversationEngineConfig(
        session_log_path=session_log_path,
        max_history_messages=max_history,
    )
    engine = ConversationEngine(engine_cfg)

    persona_words = "、".join(genome.identity.persona_keywords) or "温柔、真诚、好奇、长期陪伴"

    print("=== Universe Singularity - 对话 CLI v1.1 (Genome-driven) ===")
    print(f"当前环境: {settings.environment}")
    print(f"使用模型: {settings.openai.model}")
    print(f"Base URL : {settings.openai.base_url}")
    print(f"对话日志路径: {session_log_path}")
    print(f"历史消息上限: {max_history}")
    print()
    print("提示：输入内容回车与数字胚胎对话，输入 'exit' 或 'quit' 结束。\n")

    while True:
        try:
            text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[收到中断信号，结束对话]")
            break

        if not text:
            continue

        if text.lower() in {"exit", "quit"}:
            print("[结束对话]")
            break

        # ---------- 1) 先识别意图 ----------
        intent = classify_intent(text)
        print(f"[intent={intent.label.value}, confidence={intent.confidence:.2f}]")

        # ---------- 2) 构造上下文 ----------
        context_messages = engine.build_context_messages(text)

        # ---------- 3) 构造 system prompt（带人格 & 意图风格） ----------
        system_prompt = build_system_prompt(persona_words, intent)

        messages = [{"role": "system", "content": system_prompt}] + context_messages

        # ---------- 4) 调用模型 ----------
        response = client.chat.completions.create(
            model=settings.openai.model,
            messages=messages,
            max_tokens=256,
        )

        reply_text = response.choices[0].message.content or ""
        print(f"胚胎：{reply_text}")

        # ---------- 5) 记录本轮对话 ----------
        engine.record_interaction(text, reply_text)
        logger.info("完成一轮对话交互。")


if __name__ == "__main__":
    main()
