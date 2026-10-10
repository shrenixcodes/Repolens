"""Provider-agnostic LLM and embedding abstractions for RepoLens."""

from repolens_ai.embeddings import (
    EmbeddingProvider,
    MockEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    build_embedding_provider,
)

__all__ = [
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "build_embedding_provider",
]
