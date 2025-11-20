"""
Universe Singularity - 配置系统（Phase 0）

职责：
1. 从 YAML + 环境变量 / .env 里加载配置
2. 把配置整理成强类型的 Pydantic 对象
3. 提供 get_settings() 作为全局入口
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from . import DEFAULT_CONFIG_FILE


class OpenAISettings(BaseModel):
    """OpenAI / 代理相关配置。"""

    base_url: str = Field(..., description="OpenAI 代理的 Base URL")
    api_key: str = Field(..., description="OpenAI API Key（或代理密钥）")
    model: str = Field(..., description="默认使用的模型名称")
    timeout: int = Field(60, description="请求超时时间（秒）")


class AppSettings(BaseModel):
    """应用级配置。"""

    environment: str = Field("dev", description="当前运行环境，如 dev / prod")
    openai: OpenAISettings


def _load_yaml(path: Path) -> Dict[str, Any]:
    """安全读取 YAML 配置文件，不存在则返回空 dict。"""
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise RuntimeError(f"配置文件格式错误：{path}")

    return data


def load_settings(config_file: Optional[Path] = None) -> AppSettings:
    """
    加载全局配置（单次）：

    优先级（后者覆盖前者）：
    1. YAML 配置文件（默认 config/settings.yaml）
    2. 环境变量 / .env：
       - APP_ENVIRONMENT / ENVIRONMENT
       - OPENAI_BASE_URL
       - OPENAI_API_KEY
       - OPENAI_MODEL
       - OPENAI_TIMEOUT
    """
    # 先加载 .env
    load_dotenv()

    cfg_path = config_file or DEFAULT_CONFIG_FILE
    yaml_cfg = _load_yaml(cfg_path)

    # ---------- 环境 ----------
    env_env = os.getenv("APP_ENVIRONMENT") or os.getenv("ENVIRONMENT")
    environment = env_env or yaml_cfg.get("environment") or "dev"

    # ---------- OpenAI ----------
    yaml_openai = yaml_cfg.get("openai") or {}
    if not isinstance(yaml_openai, dict):
        raise RuntimeError("YAML 中 openai 字段必须是对象（mapping）")

    openai_cfg: Dict[str, Any] = dict(yaml_openai)

    env_overrides = {
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL"),
        "timeout": os.getenv("OPENAI_TIMEOUT"),
    }

    for key, val in env_overrides.items():
        if val is None:
            continue
        if key == "timeout":
            try:
                openai_cfg[key] = int(val)
            except ValueError as exc:
                raise RuntimeError("OPENAI_TIMEOUT 必须是整数（秒）") from exc
        else:
            openai_cfg[key] = val

    merged = {
        "environment": environment,
        "openai": openai_cfg,
    }

    try:
        return AppSettings(**merged)
    except ValidationError as exc:
        raise RuntimeError(f"配置验证失败，请检查 .env 或 YAML：\n{exc}") from exc


@lru_cache
def get_settings() -> AppSettings:
    """
    获取全局配置（带缓存）。
    后面任何地方只要调用 get_settings() 就能拿到同一个配置实例。
    """
    return load_settings()
