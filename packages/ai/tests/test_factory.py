import pytest

from repolens_ai.embeddings.factory import build_embedding_provider
from repolens_ai.embeddings.mock import MockEmbeddingProvider
from repolens_ai.embeddings.ollama import OllamaEmbeddingProvider
from repolens_ai.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider
from repolens_config.models import EmbeddingConfig
from repolens_shared.exceptions import ConfigurationError


def test_builds_mock_by_default() -> None:
    provider = build_embedding_provider(EmbeddingConfig())
    assert isinstance(provider, MockEmbeddingProvider)


def test_builds_ollama() -> None:
    provider = build_embedding_provider(EmbeddingConfig(provider="ollama", model="nomic-embed-text"))
    assert isinstance(provider, OllamaEmbeddingProvider)


def test_builds_openai_compatible() -> None:
    provider = build_embedding_provider(
        EmbeddingConfig(provider="openai_compatible", model="m", base_url="http://localhost:1234/v1")
    )
    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)


def test_unknown_provider_raises() -> None:
    config = EmbeddingConfig()
    config.provider = "nonsense"  # type: ignore[assignment]
    with pytest.raises(ConfigurationError):
        build_embedding_provider(config)
