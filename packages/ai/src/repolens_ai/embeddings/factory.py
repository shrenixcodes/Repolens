"""Turns an `EmbeddingConfig` into a concrete `EmbeddingProvider`."""

from __future__ import annotations

from repolens_ai.embeddings.base import EmbeddingProvider
from repolens_ai.embeddings.mock import MockEmbeddingProvider
from repolens_ai.embeddings.ollama import OllamaEmbeddingProvider
from repolens_ai.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider
from repolens_config.models import EmbeddingConfig
from repolens_shared.exceptions import ConfigurationError


def build_embedding_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    if config.provider == "mock":
        return MockEmbeddingProvider(model=config.model, dimensions=config.dimensions)
    if config.provider == "ollama":
        return OllamaEmbeddingProvider(
            model=config.model,
            base_url=config.base_url,
            dimensions=config.dimensions,
            timeout_seconds=config.request_timeout_seconds,
        )
    if config.provider in ("openai", "openai_compatible"):
        return OpenAICompatibleEmbeddingProvider(
            provider_name=config.provider,
            model=config.model,
            base_url=config.base_url,
            api_key=config.api_key,
            dimensions=config.dimensions,
            timeout_seconds=config.request_timeout_seconds,
        )
    raise ConfigurationError(f"Unknown embedding provider: {config.provider!r}")
