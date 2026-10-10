"""Retrieval result types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    file_path: str
    symbol_qualified_name: str | None
    start_line: int
    end_line: int
    content: str
    score: float
    sources: tuple[str, ...] = field(default_factory=tuple)
    """Which signals contributed: a subset of {"lexical", "semantic", "structural"}."""


@dataclass(frozen=True, slots=True)
class RelatedSymbolRef:
    """A symbol one hop away from a retrieved result, via the dependency graph."""

    file_path: str
    qualified_name: str
    relation: str
    """The edge kind connecting it to the seed, e.g. "calls", "called_by", "imports"."""
