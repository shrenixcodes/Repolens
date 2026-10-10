"""The embedding provider contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turns text into a fixed-length vector for semantic search.

    Implementations must raise `repolens_shared.exceptions.ProviderError` on
    failure (network error, invalid response, bad config) rather than
    letting a provider-specific exception leak -- callers only ever need to
    know "embedding failed", not which HTTP client raised it.
    """

    name: str
    model: str
    dimensions: int

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
