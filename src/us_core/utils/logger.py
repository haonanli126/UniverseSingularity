"""
通用日志工具：整个数字胚胎的「心电图记录仪」。

- 支持控制台 + 文件双通道输出
- 自动在项目根目录下创建 logs/universe_singularity.log
- 避免重复初始化（多次调用不会重复添加 handler）
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import PROJECT_ROOT

_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _get_log_file() -> Path:
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir / "universe_singularity.log"


def setup_logger(name: str | None = None) -> logging.Logger:
    """
    获取一个已经配置好的 logger。

    Parameters
    ----------
    name : str | None
        日志记录名称。如果为 None，使用项目默认名称 "universe_singularity"。

    Returns
    -------
    logging.Logger
    """
    logger_name = name or "universe_singularity"
    logger = logging.getLogger(logger_name)

    # 如果已经配置过 handler，就直接复用，避免重复输出
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（滚动日志）
    file_handler = RotatingFileHandler(
        _get_log_file(),
        maxBytes=1_000_000,  # 约 1MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 不向父 logger 传播，避免重复输出
    logger.propagate = False

    return logger
