"""Caps a ranked result list to a character budget before it reaches a prompt."""

from __future__ import annotations

from repolens_retrieval.models import RetrievedChunk


def assemble_context(chunks: list[RetrievedChunk], *, max_chars: int = 8000) -> list[RetrievedChunk]:
    """Keep highest-scored chunks until ``max_chars`` of content is reached.

    Chunks are already sorted by relevance (callers pass `hybrid_search`'s
    output); this never reorders, it only decides where to cut.
    """
    assembled: list[RetrievedChunk] = []
    used = 0
    for chunk in chunks:
        chunk_len = len(chunk.content)
        if assembled and used + chunk_len > max_chars:
            break
        assembled.append(chunk)
        used += chunk_len
    return assembled
