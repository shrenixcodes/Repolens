"""Text-generation provider for OpenAI and OpenAI-chat-API-compatible servers."""

from __future__ import annotations

from collections.abc import Iterator

import httpx

from repolens_shared.exceptions import ConfigurationError, ProviderError

OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatibleLLMProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        model: str,
        base_url: str | None,
        api_key: str | None,
        temperature: float = 0.1,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.name = provider_name
        self.model = model
        if base_url is None:
            if provider_name == "openai":
                base_url = OPENAI_DEFAULT_BASE_URL
            else:
                raise ConfigurationError(
                    "llm.base_url is required when llm.provider is 'openai_compatible'"
                )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._temperature = temperature
        self._timeout = timeout_seconds

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                json={"model": self.model, "messages": messages, "temperature": self._temperature},
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} generation request failed: {exc}") from exc

        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                f"{self.name} returned an unexpected chat completion response: {payload!r}"
            ) from exc

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        # Interface parity only -- see LLMProvider.stream docstring.
        yield self.generate(prompt, system=system)
