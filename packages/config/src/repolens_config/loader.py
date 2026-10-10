"""Layered configuration loading: defaults -> YAML file -> environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from repolens_config.models import RepoLensConfig
from repolens_shared.exceptions import ConfigurationError

_CONFIG_FILENAMES = ("repolens.yaml", "repolens.yml", ".repolens.yaml", ".repolens.yml")

# Maps environment variable name -> dotted path into the config dict.
_ENV_VAR_MAP: dict[str, tuple[str, ...]] = {
    "REPOLENS_LLM_PROVIDER": ("llm", "provider"),
    "REPOLENS_LLM_MODEL": ("llm", "model"),
    "REPOLENS_LLM_BASE_URL": ("llm", "base_url"),
    "REPOLENS_LLM_API_KEY": ("llm", "api_key"),
    "REPOLENS_EMBEDDING_PROVIDER": ("embedding", "provider"),
    "REPOLENS_EMBEDDING_MODEL": ("embedding", "model"),
    "REPOLENS_EMBEDDING_BASE_URL": ("embedding", "base_url"),
    "REPOLENS_EMBEDDING_API_KEY": ("embedding", "api_key"),
    "REPOLENS_DATABASE_PATH": ("database", "path"),
    "REPOLENS_SERVER_HOST": ("server", "host"),
    "REPOLENS_SERVER_PORT": ("server", "port"),
}

_INT_FIELDS = {("server", "port")}
_FLOAT_FIELDS = {("llm", "temperature"), ("llm", "request_timeout_seconds")}
_BOOL_FIELDS: set[tuple[str, ...]] = set()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _find_config_file(repo_root: Path) -> Path | None:
    for name in _CONFIG_FILENAMES:
        candidate = repo_root / name
        if candidate.is_file():
            return candidate
    return None


def _coerce(path: tuple[str, ...], raw_value: str) -> Any:
    if path in _INT_FIELDS:
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ConfigurationError(
                f"Environment variable for {'.'.join(path)} must be an integer, got {raw_value!r}"
            ) from exc
    if path in _FLOAT_FIELDS:
        try:
            return float(raw_value)
        except ValueError as exc:
            raise ConfigurationError(
                f"Environment variable for {'.'.join(path)} must be a float, got {raw_value!r}"
            ) from exc
    return raw_value


def _apply_env_overrides(data: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    result = {k: (dict(v) if isinstance(v, dict) else v) for k, v in data.items()}
    for env_var, path in _ENV_VAR_MAP.items():
        if env_var not in env:
            continue
        value = _coerce(path, env[env_var])
        node = result
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value
    return result


def load_config(
    repo_root: Path,
    *,
    config_path: Path | None = None,
    env: dict[str, str] | None = None,
) -> RepoLensConfig:
    """Load configuration for ``repo_root``.

    Resolution order (later wins): built-in defaults -> YAML config file
    (``config_path`` if given, otherwise the first of
    ``repolens.yaml``/``repolens.yml``/``.repolens.yaml``/``.repolens.yml``
    found in ``repo_root``) -> environment variables (``env``, defaulting to
    ``os.environ``).
    """
    defaults = RepoLensConfig().model_dump()

    file_path = config_path if config_path is not None else _find_config_file(repo_root)
    file_data: dict[str, Any] = {}
    if file_path is not None:
        if not file_path.is_file():
            raise ConfigurationError(f"Config file not found: {file_path}")
        try:
            loaded = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ConfigurationError(f"Config file {file_path} must contain a mapping at the top level")
        file_data = loaded

    merged = _deep_merge(defaults, file_data)
    merged = _apply_env_overrides(merged, env if env is not None else dict(os.environ))

    try:
        return RepoLensConfig(**merged)
    except Exception as exc:  # pydantic.ValidationError, kept generic to avoid a hard pydantic import here
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc
