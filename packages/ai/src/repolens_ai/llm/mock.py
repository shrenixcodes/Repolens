"""A deterministic, offline text-generation provider.

Does not simulate AI prose -- it returns a fixed, honest disclaimer plus a
count of how many sources were included in the prompt. RepoLens's grounding
guarantee (citations always reflect real retrieval, never fabricated files)
lives in the retrieval/citation layer regardless of which LLM provider is
selected, so this provider only needs to be deterministic and truthful
about what it is: not a real language model.
"""

from __future__ import annotations

from collections.abc import Iterator


class MockLLMProvider:
    name = "mock"

    def __init__(self, *, model: str = "mock-echo") -> None:
        self.model = model

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        source_count = sum(1 for line in prompt.splitlines() if line.startswith("Source:"))
        return (
            "No language model is configured (using the deterministic mock provider). "
            f"{source_count} supporting source(s) were retrieved from the repository -- "
            "see the citations below. Configure llm.provider (ollama, openai, or "
            "openai_compatible) in repolens.yaml for a natural-language explanation."
        )

    def stream(self, prompt: str, *, system: str | None = None) -> Iterator[str]:
        yield self.generate(prompt, system=system)
