from __future__ import annotations

"""
在项目根目录运行：

(.venv) PS D:/UniverseSingularity> python scripts/heartbeat_loop.py
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from src.us_core.core.heartbeat import run_heartbeat_cycle


def main() -> None:
    settings = get_settings()

    print("=== Universe Singularity - Heartbeat Cycle ===")
    print(f"当前环境: {settings.environment}")
    print(f"使用模型: {settings.openai.model}")
    print(f"Base URL : {settings.openai.base_url}")
    print()

    reply = run_heartbeat_cycle(cycles=3, ask_model=True)

    print("\n本轮心跳总结：")
    print(reply or "(未向模型请求总结)")


if __name__ == "__main__":
    main()
