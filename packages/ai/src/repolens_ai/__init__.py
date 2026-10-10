"""Provider-agnostic LLM and embedding abstractions for RepoLens."""

from repolens_ai.embeddings import (
    EmbeddingProvider,
    MockEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    build_embedding_provider,
)
from repolens_ai.llm import (
    LLMProvider,
    MockLLMProvider,
    OllamaLLMProvider,
    OpenAICompatibleLLMProvider,
    build_llm_provider,
)

__all__ = [
    "EmbeddingProvider",
    "LLMProvider",
    "MockEmbeddingProvider",
    "MockLLMProvider",
    "OllamaEmbeddingProvider",
    "OllamaLLMProvider",
    "OpenAICompatibleEmbeddingProvider",
    "OpenAICompatibleLLMProvider",
    "build_embedding_provider",
    "build_llm_provider",
]
