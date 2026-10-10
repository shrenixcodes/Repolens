"""Text-generation provider abstraction and implementations."""

from repolens_ai.llm.base import LLMProvider
from repolens_ai.llm.factory import build_llm_provider
from repolens_ai.llm.mock import MockLLMProvider
from repolens_ai.llm.ollama import OllamaLLMProvider
from repolens_ai.llm.openai_compatible import OpenAICompatibleLLMProvider

__all__ = [
    "LLMProvider",
    "MockLLMProvider",
    "OllamaLLMProvider",
    "OpenAICompatibleLLMProvider",
    "build_llm_provider",
]
