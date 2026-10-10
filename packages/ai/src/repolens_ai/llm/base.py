"""The text-generation provider contract."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Generates text from a prompt.

    Implementations must raise `repolens_shared.exceptions.ProviderError` on
    failure rather than letting a provider-specific exception leak.

    `stream` exists for interface parity with the product's streaming
    ambitions, but concrete HTTP-backed providers in this package currently
    implement it as a single-chunk wrapper around `generate` -- see each
    provider's docstring. True incremental token streaming is a documented
    follow-up, not something this interface pretends is already done.
    """

    name: str
    model: str

    def generate(self, prompt: str, *, system: str | None = None) -> str: ...

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]: ...
