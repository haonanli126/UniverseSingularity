from __future__ import annotations

import sys
from pathlib import Path

# 确保可以从 scripts/ 下导入新脚本
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import daily_cycle_with_reflection  # type: ignore[import]


def test_daily_cycle_with_reflection_has_main() -> None:
    """
    仅测试模块可以被导入，且存在 main 函数。
    不直接调用 main，避免在 pytest 中触发完整 daily_cycle 流程。
    """
    assert hasattr(daily_cycle_with_reflection, "main")
