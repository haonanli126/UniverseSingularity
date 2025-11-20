"""
Config package for the Universe Singularity / Digital Embryo project.

Phase 0 只做两件事：
1. 提供一个可以引用的 PROJECT_ROOT 常量
2. 约定默认的配置文件路径（settings.yaml）
"""

from pathlib import Path

# 项目根目录：.../UniverseSingularity
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

# config 目录本身
CONFIG_DIR: Path = Path(__file__).resolve().parent

# 约定的默认配置文件路径（将来你会把 settings.example.yaml 复制为 settings.yaml）
DEFAULT_CONFIG_FILE: Path = CONFIG_DIR / "settings.yaml"
