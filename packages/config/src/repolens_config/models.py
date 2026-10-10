"""Typed configuration models.

These are plain validated data containers -- loading/merging logic lives in
`repolens_config.loader`, not here, so the models stay easy to construct
directly in tests.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from repolens_config.defaults import DEFAULT_IGNORE_PATTERNS, DEFAULT_MAX_FILE_SIZE_BYTES

ProviderName = Literal["mock", "ollama", "openai", "openai_compatible"]


class LLMConfig(BaseModel):
    """Configuration for the text-generation provider.

    Defaults to ``mock`` so the application runs fully offline out of the
    box -- a cloud or local model is opt-in, never required.
    """

    provider: ProviderName = "mock"
    model: str = "llama3.1"
    base_url: str | None = None
    api_key: str | None = Field(default=None, repr=False)
    temperature: float = 0.1
    request_timeout_seconds: float = 60.0


class EmbeddingConfig(BaseModel):
    """Configuration for the embedding provider used for semantic search."""

    provider: ProviderName = "mock"
    model: str = "nomic-embed-text"
    base_url: str | None = None
    api_key: str | None = Field(default=None, repr=False)
    dimensions: int = 256
    request_timeout_seconds: float = 60.0


class IndexingConfig(BaseModel):
    """Controls what the indexer scans and how aggressively."""

    ignore: list[str] = Field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    respect_gitignore: bool = True
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES
    enable_embeddings: bool = False


class DatabaseConfig(BaseModel):
    """Where RepoLens persists its index for a given repository."""

    path: str = ".repolens/repolens.sqlite3"


class ServerConfig(BaseModel):
    """API server bind settings. Loopback-only by default."""

    host: str = "127.0.0.1"
    port: int = 8000


class RepoLensConfig(BaseModel):
    """The fully assembled, validated RepoLens configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
