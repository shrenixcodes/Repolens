"""Index status reporting (`repolens status`)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from repolens_indexer.db import IndexStore


@dataclass(frozen=True, slots=True)
class IndexStatus:
    total_files: int
    total_symbols: int
    total_relationships: int
    resolved_relationships: int
    files_by_language: dict[str, int]
    symbols_by_kind: dict[str, int]
    last_indexed_at: str | None


def get_status(store: IndexStore) -> IndexStatus:
    files = store.list_files()
    symbols = store.iter_all_symbols()
    relationships = store.iter_all_relationships()

    files_by_language = Counter(f.language or "unknown" for f in files)
    symbols_by_kind = Counter(s.kind for s in symbols)
    resolved = sum(1 for r in relationships if r.resolution == "resolved")
    last_indexed = max((f.indexed_at for f in files), default=None)

    return IndexStatus(
        total_files=len(files),
        total_symbols=len(symbols),
        total_relationships=len(relationships),
        resolved_relationships=resolved,
        files_by_language=dict(files_by_language),
        symbols_by_kind=dict(symbols_by_kind),
        last_indexed_at=last_indexed,
    )
