"""Combines lexical, semantic, and structural signals into one ranked list."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from repolens_indexer.db import IndexStore
from repolens_indexer.embeddings import semantic_search
from repolens_indexer.search import search_lexical
from repolens_retrieval.models import RetrievedChunk

_TOKEN_RE = re.compile(r"\w+")

DEFAULT_LEXICAL_WEIGHT = 0.5
DEFAULT_SEMANTIC_WEIGHT = 0.5
STRUCTURAL_BOOST = 0.25


def _normalize(scores: Sequence[float]) -> list[float]:
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [1.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def _key(file_path: str, start_line: int, end_line: int) -> tuple[str, int, int]:
    return (file_path, start_line, end_line)


def hybrid_search(
    store: IndexStore,
    query: str,
    *,
    embed_fn: Callable[[str], list[float]] | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
    limit: int = 10,
    candidate_limit: int = 50,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
) -> list[RetrievedChunk]:
    """Rank chunks for ``query`` using whichever signals are available.

    Semantic search is skipped (not an error) when ``embed_fn`` is None --
    this is how retrieval stays usable with no model configured at all.
    """
    lexical_results = search_lexical(store, query, limit=candidate_limit)

    semantic_results = []
    if embed_fn is not None and embedding_provider and embedding_model:
        query_vector = embed_fn(query)
        semantic_results = semantic_search(
            store,
            query_vector,
            provider=embedding_provider,
            model=embedding_model,
            limit=candidate_limit,
        )

    draft: dict[tuple[str, int, int], dict] = {}

    lexical_norms = _normalize([r.score for r in lexical_results])
    for result, norm_score in zip(lexical_results, lexical_norms, strict=True):
        key = _key(result.file_path, result.start_line, result.end_line)
        draft[key] = {
            "file_path": result.file_path,
            "symbol_qualified_name": result.symbol_qualified_name,
            "start_line": result.start_line,
            "end_line": result.end_line,
            "content": result.snippet,
            "lexical": norm_score,
            "semantic": 0.0,
            "sources": {"lexical"},
        }

    semantic_norms = _normalize([r.score for r in semantic_results])
    for result, norm_score in zip(semantic_results, semantic_norms, strict=True):
        key = _key(result.file_path, result.start_line, result.end_line)
        if key in draft:
            draft[key]["semantic"] = norm_score
            draft[key]["sources"].add("semantic")
        else:
            draft[key] = {
                "file_path": result.file_path,
                "symbol_qualified_name": result.symbol_qualified_name,
                "start_line": result.start_line,
                "end_line": result.end_line,
                "content": result.content,
                "lexical": 0.0,
                "semantic": norm_score,
                "sources": {"semantic"},
            }

    query_tokens = {t.lower() for t in _TOKEN_RE.findall(query)}

    results = []
    for entry in draft.values():
        score = lexical_weight * entry["lexical"] + semantic_weight * entry["semantic"]
        symbol_name = entry["symbol_qualified_name"]
        if symbol_name and symbol_name.rsplit(".", 1)[-1].lower() in query_tokens:
            score += STRUCTURAL_BOOST
            entry["sources"].add("structural")
        results.append(
            RetrievedChunk(
                file_path=entry["file_path"],
                symbol_qualified_name=symbol_name,
                start_line=entry["start_line"],
                end_line=entry["end_line"],
                content=entry["content"],
                score=score,
                sources=tuple(sorted(entry["sources"])),
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
