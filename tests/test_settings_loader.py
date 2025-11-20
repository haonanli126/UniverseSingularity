"""
对 config.settings.load_settings 做一次单元测试。

重点验证「合并逻辑」：

- YAML 给出一份完整配置
- 环境变量覆盖其中一部分字段
- 最终结果以「环境变量优先」为准
- 并且不会受到真实项目根目录 .env 的干扰
"""

from __future__ import annotations

from pathlib import Path

from config import settings as settings_mod
from config.settings import load_settings


def test_load_settings_from_yaml_and_env(tmp_path, monkeypatch):
    # 0. 屏蔽掉真实项目里的 .env 加载
    #    把 config.settings.load_dotenv 替换为一个什么都不做的函数
    monkeypatch.setattr(settings_mod, "load_dotenv", lambda *args, **kwargs: None)

    # 1. 在临时目录写一个假的 YAML 配置
    cfg_path: Path = tmp_path / "settings.yaml"
    cfg_path.write_text(
        """environment: "yaml-env"

openai:
  base_url: "https://yaml-base-url"
  api_key: "yaml-key"
  model: "yaml-model"
  timeout: 30
""",
        encoding="utf-8",
    )

    # 2. 清空跟本测试相关的环境变量，避免受外部影响
    for key in [
        "APP_ENVIRONMENT",
        "ENVIRONMENT",
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_TIMEOUT",
    ]:
        monkeypatch.delenv(key, raising=False)

    # 3. 用环境变量覆盖部分字段（模拟 .env / 真实环境）
    #    注意：我们刻意只覆盖 environment / api_key / model
    monkeypatch.setenv("APP_ENVIRONMENT", "env-env")
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    # 4. 使用临时配置文件加载
    settings = load_settings(config_file=cfg_path)

    # 5. 断言合并结果

    # environment 来自 APP_ENVIRONMENT（环境变量覆盖 YAML）
    assert settings.environment == "env-env"

    # base_url / timeout 沿用 YAML（因为我们没有用环境变量覆盖）
    assert settings.openai.base_url == "https://yaml-base-url"
    assert settings.openai.timeout == 30

    # api_key / model 被环境变量覆盖
    assert settings.openai.api_key == "env-key"
    assert settings.openai.model == "env-model"
