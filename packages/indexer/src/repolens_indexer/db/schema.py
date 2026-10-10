"""SQLite schema for the per-repository RepoLens index.

One index database lives at ``<repo>/.repolens/repolens.sqlite3`` and
describes exactly one repository -- there is no multi-tenant "repositories"
table here. Schema changes are applied by :mod:`repolens_indexer.db.engine`,
which tracks the applied version in ``schema_version`` and runs any
migrations the current database is missing.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

schema_version_table = Table(
    "schema_version",
    metadata,
    Column("version", Integer, primary_key=True),
)

files_table = Table(
    "files",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("path", String, nullable=False, unique=True),
    Column("language", String, nullable=True),
    Column("content_hash", String, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("indexed_at", String, nullable=False),
)

symbols_table = Table(
    "symbols",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_id", Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
    Column("name", String, nullable=False),
    Column("qualified_name", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("start_line", Integer, nullable=False),
    Column("end_line", Integer, nullable=False),
    Column("docstring", Text, nullable=True),
    Column("parent_qualified_name", String, nullable=True),
    Column("decorators", Text, nullable=True),  # JSON-encoded list[str]
    Column("is_exported", Boolean, nullable=False, default=False),
)

relationships_table = Table(
    "relationships",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_id", Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
    Column("kind", String, nullable=False),
    Column("source_qualified_name", String, nullable=False),
    Column("target_name", String, nullable=False),
    Column("target_file_id", Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
    Column("target_symbol_id", Integer, ForeignKey("symbols.id", ondelete="SET NULL"), nullable=True),
    Column("resolution", String, nullable=False),
    Column("start_line", Integer, nullable=False),
    Column("end_line", Integer, nullable=False),
)

imports_table = Table(
    "imports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_id", Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
    Column("module", String, nullable=False),
    Column("imported_names", Text, nullable=True),  # JSON-encoded list[str]
    Column("is_relative", Boolean, nullable=False, default=False),
    Column("start_line", Integer, nullable=False),
    Column("end_line", Integer, nullable=False),
    UniqueConstraint("file_id", "module", "start_line", name="uq_import_location"),
)

chunks_table = Table(
    "chunks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_id", Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
    Column("symbol_qualified_name", String, nullable=True),
    Column("start_line", Integer, nullable=False),
    Column("end_line", Integer, nullable=False),
    Column("content", Text, nullable=False),
)
"""Retrievable units of source text: one per top-level symbol, or one for the
whole file when it has none (e.g. markdown, config). `repolens_ai`/
`repolens_retrieval` (Milestone 8/9) key embeddings off `chunks.id`."""

CURRENT_SCHEMA_VERSION = 1
