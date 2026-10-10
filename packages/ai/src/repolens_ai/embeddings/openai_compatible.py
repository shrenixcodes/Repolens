"""Embedding provider for OpenAI and OpenAI-API-compatible servers.

Works against the real OpenAI API and against any self-hosted server that
implements the same `/embeddings` request/response shape (LM Studio, vLLM,
text-embeddings-inference, etc.) -- only `base_url` (and, for OpenAI itself,
`api_key`) differs.
"""

from __future__ import annotations

import httpx

from repolens_shared.exceptions import ConfigurationError, ProviderError

OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        model: str,
        base_url: str | None,
        api_key: str | None,
        dimensions: int,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.name = provider_name
        self.model = model
        self.dimensions = dimensions
        if base_url is None:
            if provider_name == "openai":
                base_url = OPENAI_DEFAULT_BASE_URL
            else:
                raise ConfigurationError(
                    "embedding.base_url is required when embedding.provider is "
                    "'openai_compatible'"
                )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        try:
            response = httpx.post(
                f"{self._base_url}/embeddings",
                json={"model": self.model, "input": texts},
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} embedding request failed: {exc}") from exc

        data = payload.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise ProviderError(
                f"{self.name} returned an unexpected embeddings response shape: {payload!r}"
            )
        try:
            return [item["embedding"] for item in data]
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"{self.name} embedding response missing 'embedding': {exc}") from exc
