from __future__ import annotations

"""
Universe Singularity - Genome 配置加载（数字胚胎 DNA）

读取 config/genome.yaml，并提供 get_genome() 作为全局入口。
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

from . import CONFIG_DIR


class EmbryoConfig(BaseModel):
    name: str
    codename: str
    owner: str
    description: str
    phase: int


class IdentityConfig(BaseModel):
    default_language: str = "zh-CN"
    persona_keywords: List[str] = Field(default_factory=list)
    mode: str = "default"


class PrimaryModelConfig(BaseModel):
    provider: str = "openai-compatible"
    model_name_env: str = "OPENAI_MODEL"
    max_reply_tokens: int = 512


class ModelsConfig(BaseModel):
    primary: PrimaryModelConfig


class HeartbeatConfig(BaseModel):
    enabled: bool = True
    default_cycles: int = 3
    log_to_file: bool = True


class MemoryShortTermConfig(BaseModel):
    max_events: int = 1000


class MemoryLongTermConfig(BaseModel):
    enabled: bool = True
    backend: str = "jsonl"
    path: str = "data/memory/session_log.jsonl"
    archive_path: str = "data/memory/long_term.jsonl"


class MemorySummarizationConfig(BaseModel):
    enabled: bool = True
    min_messages_for_summary: int = 6


class MemoryConfig(BaseModel):
    short_term: MemoryShortTermConfig
    long_term: MemoryLongTermConfig
    summarization: MemorySummarizationConfig


class MetacognitionStyleConfig(BaseModel):
    warmth_level: float = 0.9
    directness: float = 0.6
    depth: float = 0.7


class MetacognitionConfig(BaseModel):
    enabled: bool = True
    style: MetacognitionStyleConfig
    # 反思日志路径（相对 PROJECT_ROOT），默认值给一个合理路径
    reflection_log_path: str = "data/memory/reflections.jsonl"



class SafetyConfig(BaseModel):
    enabled: bool = True
    max_requests_per_minute: int = 60
    allow_external_tools: bool = False
    notes: List[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/universe_singularity.log"


class ConversationHistoryConfig(BaseModel):
    max_messages: int = 8


class ConversationConfig(BaseModel):
    history: ConversationHistoryConfig = ConversationHistoryConfig()


class GenomeConfig(BaseModel):
    version: str
    embryo: EmbryoConfig
    identity: IdentityConfig
    models: ModelsConfig
    heartbeat: HeartbeatConfig
    memory: MemoryConfig
    metacognition: MetacognitionConfig
    safety: SafetyConfig
    logging: LoggingConfig
    conversation: Optional[ConversationConfig] = None
    developer_notes: List[str] = Field(default_factory=list)


DEFAULT_GENOME_FILE: Path = CONFIG_DIR / "genome.yaml"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Genome 配置文件不存在：{path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise RuntimeError(f"Genome 配置文件格式错误：{path}")

    return data


def load_genome(config_file: Optional[Path] = None) -> GenomeConfig:
    """
    加载 genome.yaml，返回 GenomeConfig。

    可以在测试中传入临时 config_file，以避免依赖真实文件。
    """
    cfg_path = config_file or DEFAULT_GENOME_FILE
    raw = _load_yaml(cfg_path)

    try:
        return GenomeConfig(**raw)
    except ValidationError as exc:
        raise RuntimeError(f"Genome 配置验证失败：\n{exc}") from exc


@lru_cache
def get_genome() -> GenomeConfig:
    """
    获取全局 Genome 配置（带缓存）。
    """
    return load_genome()
