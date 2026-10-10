from pathlib import Path

import pytest

from repolens_config import load_config
from repolens_shared.exceptions import ConfigurationError


def test_defaults_are_fully_offline(tmp_path: Path) -> None:
    config = load_config(tmp_path, env={})
    assert config.llm.provider == "mock"
    assert config.embedding.provider == "mock"
    assert config.server.host == "127.0.0.1"


def test_yaml_file_overrides_defaults(tmp_path: Path) -> None:
    (tmp_path / "repolens.yaml").write_text(
        "llm:\n  provider: ollama\n  model: llama3.1\nserver:\n  port: 9000\n",
        encoding="utf-8",
    )
    config = load_config(tmp_path, env={})
    assert config.llm.provider == "ollama"
    assert config.llm.model == "llama3.1"
    assert config.server.port == 9000
    # Untouched sections keep their defaults.
    assert config.embedding.provider == "mock"


def test_env_vars_override_yaml_file(tmp_path: Path) -> None:
    (tmp_path / "repolens.yaml").write_text("llm:\n  provider: ollama\n", encoding="utf-8")
    config = load_config(tmp_path, env={"REPOLENS_LLM_PROVIDER": "openai_compatible"})
    assert config.llm.provider == "openai_compatible"


def test_env_var_int_coercion(tmp_path: Path) -> None:
    config = load_config(tmp_path, env={"REPOLENS_SERVER_PORT": "9999"})
    assert config.server.port == 9999


def test_invalid_env_int_raises_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load_config(tmp_path, env={"REPOLENS_SERVER_PORT": "not-a-number"})


def test_missing_explicit_config_path_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load_config(tmp_path, config_path=tmp_path / "does-not-exist.yaml", env={})


def test_malformed_yaml_raises_configuration_error(tmp_path: Path) -> None:
    (tmp_path / "repolens.yaml").write_text("llm: [this, is, not, a, mapping", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(tmp_path, env={})


def test_default_ignore_patterns_cover_secrets_and_deps(tmp_path: Path) -> None:
    config = load_config(tmp_path, env={})
    assert ".env" in config.indexing.ignore
    assert "node_modules" in config.indexing.ignore
    assert ".git" in config.indexing.ignore
