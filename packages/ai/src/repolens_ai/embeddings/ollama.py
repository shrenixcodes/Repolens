"""Embedding provider backed by a local (or remote) Ollama server."""

from __future__ import annotations

import httpx

from repolens_shared.exceptions import ProviderError

DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaEmbeddingProvider:
    name = "ollama"

    def __init__(
        self,
        *,
        model: str,
        base_url: str | None = None,
        dimensions: int,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout_seconds

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = httpx.post(
                f"{self._base_url}/api/embed",
                json={"model": self.model, "input": texts},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama embedding request failed: {exc}") from exc

        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise ProviderError(
                f"Ollama returned an unexpected embeddings response shape: {payload!r}"
            )
        return embeddings
