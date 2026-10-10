import pytest

from repolens_ai.llm.factory import build_llm_provider
from repolens_ai.llm.mock import MockLLMProvider
from repolens_ai.llm.ollama import OllamaLLMProvider
from repolens_ai.llm.openai_compatible import OpenAICompatibleLLMProvider
from repolens_config.models import LLMConfig
from repolens_shared.exceptions import ConfigurationError


def test_builds_mock_by_default() -> None:
    assert isinstance(build_llm_provider(LLMConfig()), MockLLMProvider)


def test_builds_ollama() -> None:
    assert isinstance(build_llm_provider(LLMConfig(provider="ollama")), OllamaLLMProvider)


def test_builds_openai_compatible() -> None:
    config = LLMConfig(provider="openai_compatible", base_url="http://localhost:1234/v1")
    assert isinstance(build_llm_provider(config), OpenAICompatibleLLMProvider)


def test_unknown_provider_raises() -> None:
    config = LLMConfig()
    config.provider = "nonsense"  # type: ignore[assignment]
    with pytest.raises(ConfigurationError):
        build_llm_provider(config)
