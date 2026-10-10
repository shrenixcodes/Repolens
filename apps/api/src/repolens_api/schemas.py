"""Typed request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RepositoryCreateRequest(BaseModel):
    path: str = Field(..., description="Absolute path to the repository on disk.")


class RepositoryResponse(BaseModel):
    id: str
    path: str
    created_at: str


class IndexResponse(BaseModel):
    files_scanned: int
    files_indexed: int
    files_unchanged: int
    files_removed: int
    files_failed: int
    errors: list[dict[str, str]]


class StatusResponse(BaseModel):
    total_files: int
    total_symbols: int
    total_relationships: int
    resolved_relationships: int
    files_by_language: dict[str, int]
    symbols_by_kind: dict[str, int]
    last_indexed_at: str | None


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class SearchResultItem(BaseModel):
    file_path: str
    symbol: str | None
    start_line: int
    end_line: int
    snippet: str
    score: float


class AskRequest(BaseModel):
    question: str


class CitationItem(BaseModel):
    path: str
    start_line: int
    end_line: int
    symbol: str | None
    excerpt: str | None


class RelatedSymbolItem(BaseModel):
    path: str
    qualified_name: str
    relation: str


class AskResponse(BaseModel):
    answer: str
    grounded: bool
    citations: list[CitationItem]
    related_symbols: list[RelatedSymbolItem]


class ImpactRequest(BaseModel):
    target: str


class ImpactResponse(BaseModel):
    target: str
    target_found: bool
    direct_dependents: list[str]
    transitive_dependents: list[str]
    related_tests: list[str]
    limitations: list[str]


class GraphNode(BaseModel):
    id: str
    node_type: str
    label: str
    path: str | None = None
    kind: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    kind: str
    resolution: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    truncated: bool


class SymbolResponse(BaseModel):
    id: int
    file_path: str
    name: str
    qualified_name: str
    kind: str
    start_line: int
    end_line: int
    docstring: str | None
    parent_qualified_name: str | None
    decorators: list[str]
    is_exported: bool


class FileResponse(BaseModel):
    path: str
    language: str | None
    size_bytes: int
    content: str | None
    symbols: list[SymbolResponse]


class CommitItem(BaseModel):
    sha: str
    author_name: str
    author_email: str
    date: str
    subject: str


class GitHistoryResponse(BaseModel):
    path: str
    commits: list[CommitItem]
