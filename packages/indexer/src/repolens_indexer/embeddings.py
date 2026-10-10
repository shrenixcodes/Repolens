"""Brute-force cosine-similarity semantic search over stored embeddings.

Deliberately simple: for the repository sizes RepoLens targets locally (tens
of thousands of chunks, not millions), scanning every stored vector in
Python is fast enough and needs no extra infrastructure. If a corpus grows
past that, swap this module's internals for a dedicated vector index --
callers only depend on `semantic_search`'s signature.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from repolens_indexer.db import IndexStore


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    file_path: str
    symbol_qualified_name: str | None
    start_line: int
    end_line: int
    content: str
    score: float


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"vector length mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_search(
    store: IndexStore,
    query_vector: Sequence[float],
    *,
    provider: str,
    model: str,
    limit: int = 20,
) -> list[SemanticSearchResult]:
    rows = store.iter_embeddings(provider=provider, model=model)
    scored = [
        SemanticSearchResult(
            file_path=row.file_path,
            symbol_qualified_name=row.symbol_qualified_name,
            start_line=row.start_line,
            end_line=row.end_line,
            content=row.content,
            score=cosine_similarity(query_vector, row.vector),
        )
        for row in rows
    ]
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]
