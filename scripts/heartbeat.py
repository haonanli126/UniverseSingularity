from __future__ import annotations

"""
手动心跳脚本：

在项目根目录运行（PowerShell）：

(.venv) PS D:/UniverseSingularity> python scripts/heartbeat.py
"""

import sys
from pathlib import Path

# 确保可以 import 到 config / src 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from src.us_core.clients.openai_client import heartbeat


def main() -> None:
    settings = get_settings()

    print("=== Universe Singularity - OpenAI Heartbeat ===")
    print(f"当前环境: {settings.environment}")
    print(f"使用模型: {settings.openai.model}")
    print(f"Base URL : {settings.openai.base_url}")
    print("发送心跳请求...\n")

    reply = heartbeat("这里是浩楠，给你打一记心跳测试。")

    print("模型返回：")
    print(reply)


if __name__ == "__main__":
    main()
