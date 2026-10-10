"""Text-generation provider backed by a local (or remote) Ollama server."""

from __future__ import annotations

from collections.abc import Iterator

import httpx

from repolens_shared.exceptions import ProviderError

DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaLLMProvider:
    name = "ollama"

    def __init__(
        self,
        *,
        model: str,
        base_url: str | None = None,
        temperature: float = 0.1,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.model = model
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._temperature = temperature
        self._timeout = timeout_seconds

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system or "",
                    "stream": False,
                    "options": {"temperature": self._temperature},
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama generation request failed: {exc}") from exc

        text = payload.get("response")
        if not isinstance(text, str):
            raise ProviderError(f"Ollama returned an unexpected generate response: {payload!r}")
        return text

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        # Interface parity only -- see LLMProvider.stream docstring.
        yield self.generate(prompt, system=system)
