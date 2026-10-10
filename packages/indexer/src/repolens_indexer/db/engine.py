"""Engine creation and schema migration for the per-repository index database."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, insert, select, text

from repolens_indexer.db.schema import CURRENT_SCHEMA_VERSION, metadata, schema_version_table

# Each entry upgrades the database from (index) to (index + 1). Migration 0
# is the initial schema creation; later entries would run `ALTER TABLE`
# statements against an already-populated database. Keeping this as an
# explicit, ordered list (rather than a single `create_all`) means a
# database created with an older RepoLens version can be upgraded in place
# instead of requiring a full re-index.
_MigrationFn = Callable[[Engine], None]


def _migration_0_initial_schema(engine: Engine) -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5("
                "content, chunk_id UNINDEXED, file_path UNINDEXED, "
                "symbol_qualified_name UNINDEXED, start_line UNINDEXED, end_line UNINDEXED, "
                "tokenize='porter unicode61'"
                ")"
            )
        )


_MIGRATIONS: list[_MigrationFn] = [
    _migration_0_initial_schema,
]


def get_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


def ensure_schema(engine: Engine) -> None:
    """Create the schema if missing, or apply any pending migrations."""
    with engine.connect() as conn:
        has_version_table = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        ).fetchone()
        current_version = 0
        if has_version_table:
            row = conn.execute(select(schema_version_table.c.version)).fetchone()
            current_version = row[0] if row else 0

    if current_version >= CURRENT_SCHEMA_VERSION:
        return

    # Each migration manages its own connection/transaction (DDL via
    # `metadata.create_all` opens one internally), so this loop must not
    # already be holding a transaction on the same engine.
    for version in range(current_version, CURRENT_SCHEMA_VERSION):
        _MIGRATIONS[version](engine)

    with engine.begin() as conn:
        if current_version == 0:
            conn.execute(insert(schema_version_table).values(version=CURRENT_SCHEMA_VERSION))
        else:
            conn.execute(schema_version_table.update().values(version=CURRENT_SCHEMA_VERSION))
