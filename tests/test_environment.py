"""
Phase 0 - S01 环境自检：

1. Python 版本是否 >= 3.11
2. 项目目录结构是否存在（src / tests）
3. logger 能否正常初始化并写入一条日志
"""

from __future__ import annotations

import sys
from pathlib import Path


def test_python_version():
    major, minor = sys.version_info.major, sys.version_info.minor
    assert (major, minor) >= (3, 11), f"Python 版本过低：{major}.{minor}，请使用 >= 3.11"


def test_project_structure_exists():
    from config import PROJECT_ROOT

    assert PROJECT_ROOT.exists(), "PROJECT_ROOT 不存在"
    assert (PROJECT_ROOT / "src").exists(), "缺少 src 目录"
    assert (PROJECT_ROOT / "tests").exists(), "缺少 tests 目录"


def test_logger_setup(tmp_path: Path):
    # 导入在 src 下的 logger
    from src.us_core.utils.logger import setup_logger

    logger = setup_logger("test_environment")

    logger.info("Universe Singularity: environment smoke test.")

    # 如果跑到这里没抛异常，就说明 logger 基本可用
    assert logger is not None
