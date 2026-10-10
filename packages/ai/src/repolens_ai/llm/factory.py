"""Turns an `LLMConfig` into a concrete `LLMProvider`."""

from __future__ import annotations

from repolens_ai.llm.base import LLMProvider
from repolens_ai.llm.mock import MockLLMProvider
from repolens_ai.llm.ollama import OllamaLLMProvider
from repolens_ai.llm.openai_compatible import OpenAICompatibleLLMProvider
from repolens_config.models import LLMConfig
from repolens_shared.exceptions import ConfigurationError


def build_llm_provider(config: LLMConfig) -> LLMProvider:
    if config.provider == "mock":
        return MockLLMProvider(model=config.model)
    if config.provider == "ollama":
        return OllamaLLMProvider(
            model=config.model,
            base_url=config.base_url,
            temperature=config.temperature,
            timeout_seconds=config.request_timeout_seconds,
        )
    if config.provider in ("openai", "openai_compatible"):
        return OpenAICompatibleLLMProvider(
            provider_name=config.provider,
            model=config.model,
            base_url=config.base_url,
            api_key=config.api_key,
            temperature=config.temperature,
            timeout_seconds=config.request_timeout_seconds,
        )
    raise ConfigurationError(f"Unknown LLM provider: {config.provider!r}")
