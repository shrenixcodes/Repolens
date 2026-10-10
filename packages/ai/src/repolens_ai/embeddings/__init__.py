"""Embedding provider abstraction and implementations."""

from repolens_ai.embeddings.base import EmbeddingProvider
from repolens_ai.embeddings.factory import build_embedding_provider
from repolens_ai.embeddings.mock import MockEmbeddingProvider
from repolens_ai.embeddings.ollama import OllamaEmbeddingProvider
from repolens_ai.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "build_embedding_provider",
]
