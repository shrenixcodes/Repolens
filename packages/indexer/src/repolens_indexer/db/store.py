"""The symbol/relationship persistence layer.

`IndexStore` is the only thing in the indexer that speaks SQL. Everything
else (the pipeline, the CLI, the API) goes through it, so query shape and
schema details stay in one place.
"""

from __future__ import annotations

import array
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Engine, delete, insert, select, text, update

from repolens_indexer.chunking import ChunkDraft
from repolens_indexer.db.engine import ensure_schema, get_engine
from repolens_indexer.db.schema import (
    chunks_table,
    embeddings_table,
    files_table,
    imports_table,
    relationships_table,
    symbols_table,
)
from repolens_parser.models import ParsedImport, ParsedRelationship, ParsedSymbol


@dataclass(frozen=True, slots=True)
class FileRow:
    id: int
    path: str
    language: str | None
    content_hash: str
    size_bytes: int
    indexed_at: str


@dataclass(frozen=True, slots=True)
class SymbolRow:
    id: int
    file_id: int
    file_path: str
    name: str
    qualified_name: str
    kind: str
    start_line: int
    end_line: int
    docstring: str | None
    parent_qualified_name: str | None
    decorators: tuple[str, ...]
    is_exported: bool


@dataclass(frozen=True, slots=True)
class EmbeddingRow:
    chunk_id: int
    file_path: str
    symbol_qualified_name: str | None
    start_line: int
    end_line: int
    content: str
    vector: list[float]


@dataclass(frozen=True, slots=True)
class RelationshipRow:
    id: int
    file_id: int
    file_path: str
    kind: str
    source_qualified_name: str
    target_name: str
    target_file_id: int | None
    target_symbol_id: int | None
    resolution: str
    start_line: int
    end_line: int


class IndexStore:
    """Persistence for one repository's index database."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        ensure_schema(engine)

    @classmethod
    def open(cls, db_path: Path) -> IndexStore:
        return cls(get_engine(db_path))

    def close(self) -> None:
        self._engine.dispose()

    # -- files ---------------------------------------------------------

    def upsert_file(
        self, *, path: str, language: str | None, content_hash: str, size_bytes: int
    ) -> int:
        indexed_at = datetime.now(timezone.utc).isoformat()
        with self._engine.begin() as conn:
            existing = conn.execute(
                select(files_table.c.id).where(files_table.c.path == path)
            ).fetchone()
            if existing is not None:
                conn.execute(
                    update(files_table)
                    .where(files_table.c.id == existing.id)
                    .values(
                        language=language,
                        content_hash=content_hash,
                        size_bytes=size_bytes,
                        indexed_at=indexed_at,
                    )
                )
                return int(existing.id)

            result = conn.execute(
                insert(files_table).values(
                    path=path,
                    language=language,
                    content_hash=content_hash,
                    size_bytes=size_bytes,
                    indexed_at=indexed_at,
                )
            )
            inserted_pk = result.inserted_primary_key
            assert inserted_pk is not None
            return int(inserted_pk[0])

    def get_file(self, path: str) -> FileRow | None:
        with self._engine.connect() as conn:
            row = conn.execute(select(files_table).where(files_table.c.path == path)).fetchone()
        return self._file_row(row) if row else None

    def list_files(self) -> list[FileRow]:
        with self._engine.connect() as conn:
            rows = conn.execute(select(files_table).order_by(files_table.c.path)).fetchall()
        return [self._file_row(r) for r in rows]

    def delete_file(self, path: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(files_table).where(files_table.c.path == path))

    @staticmethod
    def _file_row(row) -> FileRow:  # type: ignore[no-untyped-def]
        return FileRow(
            id=row.id,
            path=row.path,
            language=row.language,
            content_hash=row.content_hash,
            size_bytes=row.size_bytes,
            indexed_at=row.indexed_at,
        )

    # -- symbols ---------------------------------------------------------

    def replace_file_symbols(self, file_id: int, symbols: Iterable[ParsedSymbol]) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(symbols_table).where(symbols_table.c.file_id == file_id))
            rows = [
                {
                    "file_id": file_id,
                    "name": s.name,
                    "qualified_name": s.qualified_name,
                    "kind": s.kind.value,
                    "start_line": s.location.start_line,
                    "end_line": s.location.end_line,
                    "docstring": s.docstring,
                    "parent_qualified_name": s.parent_qualified_name,
                    "decorators": json.dumps(list(s.decorators)),
                    "is_exported": s.is_exported,
                }
                for s in symbols
            ]
            if rows:
                conn.execute(insert(symbols_table), rows)

    def list_symbols_for_file(self, file_id: int) -> list[SymbolRow]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(symbols_table, files_table.c.path)
                .join(files_table, files_table.c.id == symbols_table.c.file_id)
                .where(symbols_table.c.file_id == file_id)
            ).fetchall()
        return [self._symbol_row(r) for r in rows]

    def iter_all_symbols(self) -> list[SymbolRow]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(symbols_table, files_table.c.path).join(
                    files_table, files_table.c.id == symbols_table.c.file_id
                )
            ).fetchall()
        return [self._symbol_row(r) for r in rows]

    @staticmethod
    def _symbol_row(row) -> SymbolRow:  # type: ignore[no-untyped-def]
        return SymbolRow(
            id=row.id,
            file_id=row.file_id,
            file_path=row.path,
            name=row.name,
            qualified_name=row.qualified_name,
            kind=row.kind,
            start_line=row.start_line,
            end_line=row.end_line,
            docstring=row.docstring,
            parent_qualified_name=row.parent_qualified_name,
            decorators=tuple(json.loads(row.decorators)) if row.decorators else (),
            is_exported=bool(row.is_exported),
        )

    # -- relationships ---------------------------------------------------

    def replace_file_relationships(
        self, file_id: int, relationships: Iterable[ParsedRelationship]
    ) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(relationships_table).where(relationships_table.c.file_id == file_id))
            rows = [
                {
                    "file_id": file_id,
                    "kind": r.kind.value,
                    "source_qualified_name": r.source_qualified_name,
                    "target_name": r.target_name,
                    "target_file_id": None,
                    "target_symbol_id": None,
                    "resolution": r.resolution.value,
                    "start_line": r.location.start_line,
                    "end_line": r.location.end_line,
                }
                for r in relationships
            ]
            if rows:
                conn.execute(insert(relationships_table), rows)

    def iter_all_relationships(self) -> list[RelationshipRow]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(relationships_table, files_table.c.path).join(
                    files_table, files_table.c.id == relationships_table.c.file_id
                )
            ).fetchall()
        return [self._relationship_row(r) for r in rows]

    @staticmethod
    def _relationship_row(row) -> RelationshipRow:  # type: ignore[no-untyped-def]
        return RelationshipRow(
            id=row.id,
            file_id=row.file_id,
            file_path=row.path,
            kind=row.kind,
            source_qualified_name=row.source_qualified_name,
            target_name=row.target_name,
            target_file_id=row.target_file_id,
            target_symbol_id=row.target_symbol_id,
            resolution=row.resolution,
            start_line=row.start_line,
            end_line=row.end_line,
        )

    def update_relationship_resolution(
        self, relationship_id: int, *, target_file_id: int, target_symbol_id: int | None = None
    ) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                update(relationships_table)
                .where(relationships_table.c.id == relationship_id)
                .values(
                    target_file_id=target_file_id,
                    target_symbol_id=target_symbol_id,
                    resolution="resolved",
                )
            )

    # -- imports -----------------------------------------------------------

    def replace_file_imports(self, file_id: int, imports: Iterable[ParsedImport]) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(imports_table).where(imports_table.c.file_id == file_id))
            rows = [
                {
                    "file_id": file_id,
                    "module": i.module,
                    "imported_names": json.dumps(list(i.imported_names)),
                    "is_relative": i.is_relative,
                    "start_line": i.location.start_line,
                    "end_line": i.location.end_line,
                }
                for i in imports
            ]
            if rows:
                conn.execute(insert(imports_table), rows)

    # -- chunks (full-text search) ----------------------------------------

    def replace_file_chunks(
        self, file_id: int, file_path: str, chunks: Iterable[ChunkDraft]
    ) -> list[int]:
        """Replace all chunks for ``file_id``, returning the new chunk ids in
        the same order as ``chunks`` (so callers can embed chunk[i] and
        store the vector against chunk_ids[i])."""
        chunk_ids: list[int] = []
        with self._engine.begin() as conn:
            conn.execute(delete(chunks_table).where(chunks_table.c.file_id == file_id))
            conn.execute(text("DELETE FROM chunks_fts WHERE file_path = :path"), {"path": file_path})

            for chunk in chunks:
                result = conn.execute(
                    insert(chunks_table).values(
                        file_id=file_id,
                        symbol_qualified_name=chunk.symbol_qualified_name,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        content=chunk.content,
                    )
                )
                inserted_pk = result.inserted_primary_key
                assert inserted_pk is not None
                chunk_id = int(inserted_pk[0])
                chunk_ids.append(chunk_id)
                conn.execute(
                    text(
                        "INSERT INTO chunks_fts "
                        "(content, chunk_id, file_path, symbol_qualified_name, start_line, end_line) "
                        "VALUES (:content, :chunk_id, :file_path, :symbol_qualified_name, "
                        ":start_line, :end_line)"
                    ),
                    {
                        "content": chunk.content,
                        "chunk_id": chunk_id,
                        "file_path": file_path,
                        "symbol_qualified_name": chunk.symbol_qualified_name,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    },
                )
        return chunk_ids

    def search_chunks_fts(self, fts_query: str, *, limit: int = 20) -> list[dict]:
        """Run a raw FTS5 MATCH query. See `repolens_indexer.search` for the
        higher-level, query-sanitizing entry point -- this is intentionally
        low-level so the FTS syntax stays contained to this module."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT chunk_id, file_path, symbol_qualified_name, start_line, end_line, "
                    "content, bm25(chunks_fts) AS rank "
                    "FROM chunks_fts WHERE chunks_fts MATCH :query "
                    "ORDER BY rank LIMIT :limit"
                ),
                {"query": fts_query, "limit": limit},
            ).mappings()
            return [dict(row) for row in rows]

    # -- embeddings (semantic search) -------------------------------------

    def replace_chunk_embedding(
        self, chunk_id: int, *, provider: str, model: str, vector: list[float]
    ) -> None:
        packed = array.array("f", vector).tobytes()
        with self._engine.begin() as conn:
            conn.execute(
                delete(embeddings_table).where(
                    (embeddings_table.c.chunk_id == chunk_id)
                    & (embeddings_table.c.provider == provider)
                    & (embeddings_table.c.model == model)
                )
            )
            conn.execute(
                insert(embeddings_table).values(
                    chunk_id=chunk_id,
                    provider=provider,
                    model=model,
                    dimensions=len(vector),
                    vector=packed,
                )
            )

    def iter_embeddings(self, *, provider: str, model: str) -> list[EmbeddingRow]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(
                    embeddings_table.c.chunk_id,
                    embeddings_table.c.vector,
                    chunks_table.c.symbol_qualified_name,
                    chunks_table.c.start_line,
                    chunks_table.c.end_line,
                    chunks_table.c.content,
                    files_table.c.path,
                )
                .select_from(embeddings_table)
                .join(chunks_table, chunks_table.c.id == embeddings_table.c.chunk_id)
                .join(files_table, files_table.c.id == chunks_table.c.file_id)
                .where(embeddings_table.c.provider == provider)
                .where(embeddings_table.c.model == model)
            ).fetchall()

        return [
            EmbeddingRow(
                chunk_id=row.chunk_id,
                file_path=row.path,
                symbol_qualified_name=row.symbol_qualified_name,
                start_line=row.start_line,
                end_line=row.end_line,
                content=row.content,
                vector=array.array("f", row.vector).tolist(),
            )
            for row in rows
        ]
