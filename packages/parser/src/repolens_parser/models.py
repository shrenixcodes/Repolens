"""The parser's output domain model.

These types are intentionally storage-agnostic: `repolens_indexer` persists
them, `repolens_graph` builds a graph from them, but this module has no
knowledge of either.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from repolens_shared.types import SourceLocation


class _StrEnum(str, Enum):
    """`str`-valued enum, compatible with Python 3.10 (``enum.StrEnum`` needs 3.11+)."""

    def __str__(self) -> str:
        return str(self.value)


class SymbolKind(_StrEnum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    INTERFACE = "interface"
    TYPE_ALIAS = "type_alias"
    VARIABLE = "variable"


class RelationshipKind(_StrEnum):
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"


class ResolutionStatus(_StrEnum):
    """How confidently a relationship's target is known.

    Parsers only ever produce ``UNRESOLVED`` -- they see one file at a time
    and record the target exactly as written (a name, not a symbol).
    Cross-file resolution to a concrete symbol (upgrading to ``RESOLVED``)
    happens in `repolens_graph`, which has repository-wide visibility.
    """

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ParsedSymbol:
    name: str
    qualified_name: str
    kind: SymbolKind
    location: SourceLocation
    docstring: str | None = None
    parent_qualified_name: str | None = None
    decorators: tuple[str, ...] = ()
    is_exported: bool = False


@dataclass(frozen=True, slots=True)
class ParsedImport:
    module: str
    location: SourceLocation
    imported_names: tuple[str, ...] = ()
    is_relative: bool = False


@dataclass(frozen=True, slots=True)
class ParsedRelationship:
    kind: RelationshipKind
    source_qualified_name: str
    target_name: str
    location: SourceLocation
    resolution: ResolutionStatus = ResolutionStatus.UNRESOLVED


@dataclass
class ParseResult:
    path: str
    language: str
    symbols: list[ParsedSymbol] = field(default_factory=list)
    relationships: list[ParsedRelationship] = field(default_factory=list)
    imports: list[ParsedImport] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors
