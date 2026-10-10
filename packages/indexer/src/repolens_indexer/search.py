"""Lexical (full-text) search over indexed chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from repolens_indexer.db import IndexStore

_TOKEN_RE = re.compile(r"\w+")
_MAX_SNIPPET_CHARS = 240


@dataclass(frozen=True, slots=True)
class LexicalSearchResult:
    file_path: str
    symbol_qualified_name: str | None
    start_line: int
    end_line: int
    snippet: str
    score: float


def _build_fts_query(raw_query: str) -> str | None:
    """Turn a free-text user query into a safe FTS5 query.

    Tokenizes and OR-joins terms as quoted literals so punctuation in the
    user's query (parentheses, colons, quotes) can never be interpreted as
    FTS5 query syntax -- the user's intent is "match any of these words",
    not "run this FTS5 expression".
    """
    tokens = _TOKEN_RE.findall(raw_query)
    if not tokens:
        return None
    return " OR ".join(f'"{t}"' for t in tokens)


def _snippet(content: str, max_chars: int = _MAX_SNIPPET_CHARS) -> str:
    stripped = content.strip()
    if len(stripped) <= max_chars:
        return stripped
    return stripped[:max_chars].rstrip() + " ..."


def search_lexical(store: IndexStore, query: str, *, limit: int = 20) -> list[LexicalSearchResult]:
    """Search indexed chunk content for ``query``.

    Returns an empty list for an empty/punctuation-only query rather than
    matching everything.
    """
    fts_query = _build_fts_query(query)
    if fts_query is None:
        return []

    rows = store.search_chunks_fts(fts_query, limit=limit)
    return [
        LexicalSearchResult(
            file_path=row["file_path"],
            symbol_qualified_name=row["symbol_qualified_name"],
            start_line=row["start_line"],
            end_line=row["end_line"],
            snippet=_snippet(row["content"]),
            score=-float(row["rank"]),  # bm25 is "lower is better"; flip so higher is better
        )
        for row in rows
    ]
