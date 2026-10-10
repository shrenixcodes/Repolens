"""Splits a parsed file into retrievable chunks of source text.

One chunk per top-level-or-nested symbol (its exact source lines), or a
single whole-file chunk when the file has no extracted symbols (markdown,
JSON, config files, or a language RepoLens doesn't parse) so non-code files
stay searchable too.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from repolens_parser.models import ParsedSymbol, SymbolKind

_SKIPPED_KINDS = {SymbolKind.VARIABLE}


@dataclass(frozen=True, slots=True)
class ChunkDraft:
    symbol_qualified_name: str | None
    start_line: int
    end_line: int
    content: str


def build_chunks(source: str, symbols: Iterable[ParsedSymbol]) -> list[ChunkDraft]:
    lines = source.splitlines()
    chunks: list[ChunkDraft] = []

    for symbol in symbols:
        if symbol.kind in _SKIPPED_KINDS:
            continue
        start, end = symbol.location.start_line, symbol.location.end_line
        content = "\n".join(lines[max(start - 1, 0) : end])
        if content.strip():
            chunks.append(ChunkDraft(symbol.qualified_name, start, end, content))

    if not chunks and source.strip():
        chunks.append(ChunkDraft(None, 1, max(len(lines), 1), source))

    return chunks
