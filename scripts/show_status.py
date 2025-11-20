from __future__ import annotations

"""
数字胚胎状态面板（Status Dashboard v0）：

在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/show_status.py
"""

import sys
from pathlib import Path

from datetime import timezone

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import PROJECT_ROOT
from config.settings import get_settings
from config.genome import get_genome
from src.us_core.core.status import (
    get_conversation_stats,
    get_reflection_stats,
)
from src.us_core.utils.logger import setup_logger


def _fmt_dt(dt):
    if dt is None:
        return "（无记录）"
    # 转成本地时间友好一点（简单用本地时区）
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def main() -> None:
    settings = get_settings()
    genome = get_genome()
    logger = setup_logger("show_status")

    session_log_path = PROJECT_ROOT / Path(genome.memory.long_term.path)
    reflection_log_path = PROJECT_ROOT / Path(genome.metacognition.reflection_log_path)

    conv_stats = get_conversation_stats(session_log_path) if session_log_path.exists() else None
    refl_stats = get_reflection_stats(reflection_log_path) if reflection_log_path.exists() else None

    print("=== Universe Singularity - Status Dashboard v0 ===")
    print(f"胚胎名称: {genome.embryo.name}")
    print(f"代号: {genome.embryo.codename}")
    print(f"Owner: {genome.embryo.owner}")
    print(f"当前 Phase: {genome.embryo.phase}")
    print(f"运行环境: {settings.environment}")
    print()

    print("--- 对话统计 ---")
    if conv_stats is None:
        print(f"会话日志不存在：{session_log_path}")
    else:
        print(f"日志路径: {session_log_path}")
        print(f"事件总数: {conv_stats.total_events}")
        print(f"消息条数: {conv_stats.total_messages}")
        print(f"最近一条事件时间: {_fmt_dt(conv_stats.last_timestamp)}")
    print()

    print("--- 自省统计 ---")
    if refl_stats is None:
        print(f"自省日志不存在：{reflection_log_path}")
    else:
        print(f"日志路径: {reflection_log_path}")
        print(f"自省条数: {refl_stats.total_events}")
        print(f"最近一次自省时间: {_fmt_dt(refl_stats.last_timestamp)}")
    print()

    logger.info("展示了一次状态面板。")


if __name__ == "__main__":
    main()
