from __future__ import annotations

"""
测试 config.genome.load_genome 的基本行为：

- 能从给定 YAML 文件加载 GenomeConfig
- 关键字段正确解析（embryo/identity/memory/...）
"""

from pathlib import Path

from config.genome import GenomeConfig, load_genome


def test_load_genome_from_yaml(tmp_path: Path):
    cfg_path = tmp_path / "genome.yaml"
    cfg_path.write_text(
        """
version: "0.1.0"

embryo:
  name: "Test Embryo"
  codename: "TEST"
  owner: "Tester"
  description: "for unit test"
  phase: 1

identity:
  default_language: "zh-CN"
  persona_keywords:
    - 温柔
    - 真诚
  mode: "test_mode"

models:
  primary:
    provider: "openai-compatible"
    model_name_env: "OPENAI_MODEL"
    max_reply_tokens: 256

heartbeat:
  enabled: true
  default_cycles: 3
  log_to_file: true

memory:
  short_term:
    max_events: 100
  long_term:
    enabled: true
    backend: "jsonl"
    path: "data/memory/test_log.jsonl"
  summarization:
    enabled: true
    min_messages_for_summary: 4

metacognition:
  enabled: true
  style:
    warmth_level: 0.8
    directness: 0.5
    depth: 0.9

safety:
  enabled: true
  max_requests_per_minute: 30
  allow_external_tools: false
  notes:
    - "test note"

logging:
  level: "DEBUG"
  file: "logs/test.log"

conversation:
  history:
    max_messages: 5

developer_notes:
  - "for tests"
""",
        encoding="utf-8",
    )

    genome: GenomeConfig = load_genome(config_file=cfg_path)

    assert genome.version == "0.1.0"
    assert genome.embryo.owner == "Tester"
    assert genome.identity.mode == "test_mode"
    assert genome.memory.long_term.path == "data/memory/test_log.jsonl"
    assert genome.conversation is not None
    assert genome.conversation.history.max_messages == 5
    assert genome.logging.level == "DEBUG"
    assert genome.metacognition.reflection_log_path == "data/memory/reflections.jsonl"
    assert genome.memory.long_term.archive_path == "data/memory/long_term.jsonl"
