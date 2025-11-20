from __future__ import annotations

"""
对话 CLI · Workspace 驱动版 v0

和原来的 dialog_cli.py 差别：

- 每轮对话前，先构建一次「全局工作空间」：
  - 最近对话
  - 长期记忆
  - 最近自省
  - 心境提示（最近主导 intent）
- 把这些信息整合进 system prompt，让回复更「知情」一些
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
from src.us_core.core.workspace import build_workspace_state


def _build_workspace_context_text(ws) -> str:
    """
    把 WorkspaceState 转成一段给模型看的「内部说明文字」。

    注意：这段会写进 system prompt，模型可以参考，但不要求逐条复述。
    """
    lines: list[str] = []

    if ws.mood_hint:
        lines.append(f"- 你对用户当前整体心境的感觉是：{ws.mood_hint}")

    if ws.long_term_memories:
        lines.append("- 你曾经为这位用户记录过这些长期重要记忆：")
        for item in ws.long_term_memories[:3]:
            lines.append(f"  * [{item.intent_label}] {item.text}")

    if ws.last_reflection:
        snippet = ws.last_reflection.strip()
        if len(snippet) > 150:
            snippet = snippet[:147] + "..."
        lines.append("- 你最近一次自省的大意是：")
        lines.append(f"  {snippet}")

    if not lines:
        return "（当前没有特别突出的长期记忆或自省内容可供参考。）"

    return "\n".join(lines)


def main() -> None:
    settings = get_settings()
    genome = get_genome()

    logger = setup_logger("dialog_cli_ws")
    client = get_openai_client()

    # 会话日志路径
    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    # 长期记忆路径
    long_term_path = PROJECT_ROOT / Path(genome.memory.long_term.archive_path)
    # 自省日志路径
    reflection_path = PROJECT_ROOT / Path(genome.metacognition.reflection_log_path)

    # 对话历史长度
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

    print("=== Universe Singularity - 对话 CLI v2.0 (Workspace-driven) ===")
    print(f"当前环境: {settings.environment}")
    print(f"使用模型: {settings.openai.model}")
    print(f"Base URL : {settings.openai.base_url}")
    print(f"会话日志路径: {session_log_path}")
    print(f"长期记忆路径: {long_term_path}")
    print(f"自省日志路径: {reflection_path}")
    print(f"历史消息上限: {max_history}")
    print()
    print("提示：输入内容回车与数字胚胎对话，输入 'exit' 或 'quit' 结束。")
    print("（本版本会在内部参考全局工作空间：长期记忆 / 自省 / 心境提示）\n")

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

        # ---------- 1) 构建全局工作空间快照 ----------
        ws = build_workspace_state(
            session_log_path=session_log_path,
            long_term_path=long_term_path,
            reflection_path=reflection_path,
            max_recent_messages=max_history,
            max_long_term=5,
        )

        # ---------- 2) 识别本轮用户意图 ----------
        intent = classify_intent(text)
        print(f"[intent={intent.label.value}, confidence={intent.confidence:.2f}]")

        # ---------- 3) 构造短期上下文 ----------
        context_messages = engine.build_context_messages(text)

        # ---------- 4) 构造带 Workspace 的 system prompt ----------
        base_system = build_system_prompt(persona_words, intent)
        workspace_context = _build_workspace_context_text(ws)

        system_prompt = (
            base_system
            + "\n\n"
            "下面是你当前全局工作空间中的一些关键信息（心境 / 长期记忆 / 最近自省），"
            "这些是你「已经知道并在意」的内容，请在回应用户时参考，但不要逐条机械地复述：\n"
            f"{workspace_context}"
        )

        messages = [{"role": "system", "content": system_prompt}] + context_messages

        # ---------- 5) 调用模型 ----------
        response = client.chat.completions.create(
            model=settings.openai.model,
            messages=messages,
            max_tokens=256,
        )

        reply_text = response.choices[0].message.content or ""
        print(f"胚胎：{reply_text}")

        # ---------- 6) 记录本轮对话 ----------
        engine.record_interaction(text, reply_text)
        logger.info("完成一轮 workspace 驱动的对话交互。")


if __name__ == "__main__":
    main()
