"""A deterministic, offline embedding provider.

Not a real semantic model -- it hashes tokens into a fixed-length vector, so
texts sharing words end up with non-trivial cosine similarity (useful for
exercising the retrieval pipeline in tests) while texts with nothing in
common do not. This is the default provider so RepoLens works end-to-end
with zero network access and zero setup; swap in `ollama` or
`openai_compatible` for real semantic search.
"""

from __future__ import annotations

import hashlib
import math
import re

_TOKEN_RE = re.compile(r"\w+")


class MockEmbeddingProvider:
    name = "mock"

    def __init__(self, *, model: str = "mock-hash-embedding", dimensions: int = 256) -> None:
        self.model = model
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
