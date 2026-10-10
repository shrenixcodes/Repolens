"""Orchestrates discovery -> parsing -> persistence, incrementally.

A file is only re-parsed when its content hash changed since the last run.
Files that disappeared from disk since the last run are removed from the
index (and, via `ON DELETE CASCADE`, their symbols/relationships/imports).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from repolens_config.models import RepoLensConfig
from repolens_indexer.chunking import build_chunks
from repolens_indexer.db import IndexStore
from repolens_indexer.discovery import discover_files
from repolens_parser.registry import ParserRegistry, build_default_registry
from repolens_shared.hashing import content_hash
from repolens_shared.paths import resolve_within_root


@dataclass
class IndexResult:
    files_scanned: int = 0
    files_indexed: int = 0
    files_unchanged: int = 0
    files_removed: int = 0
    files_failed: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)


def index_db_path(repo_root: Path, config: RepoLensConfig) -> Path:
    return resolve_within_root(repo_root, config.database.path)


def run_index(
    repo_root: Path, config: RepoLensConfig, *, registry: ParserRegistry | None = None
) -> IndexResult:
    repo_root = repo_root.resolve()
    registry = registry or build_default_registry()
    store = IndexStore.open(index_db_path(repo_root, config))
    result = IndexResult()

    try:
        discovered = discover_files(repo_root, config.indexing)
        discovered_paths = {f.relative_path for f in discovered}
        result.files_scanned = len(discovered)

        for discovered_file in discovered:
            try:
                raw = discovered_file.absolute_path.read_bytes()
            except OSError as exc:
                result.files_failed += 1
                result.errors.append((discovered_file.relative_path, f"could not read file: {exc}"))
                continue

            new_hash = content_hash(raw)
            existing = store.get_file(discovered_file.relative_path)
            if existing is not None and existing.content_hash == new_hash:
                result.files_unchanged += 1
                continue

            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                # Binary file: index its existence but not its content.
                store.upsert_file(
                    path=discovered_file.relative_path,
                    language=None,
                    content_hash=new_hash,
                    size_bytes=discovered_file.size_bytes,
                )
                result.files_indexed += 1
                continue

            parser = registry.get_for_path(discovered_file.relative_path)
            language = parser.language if parser else None

            symbols = relationships = imports = ()
            if parser is not None:
                parse_result = parser.parse(discovered_file.relative_path, text)
                symbols, relationships, imports = (
                    parse_result.symbols,
                    parse_result.relationships,
                    parse_result.imports,
                )
                if parse_result.errors:
                    result.files_failed += 1
                    result.errors.extend(
                        (discovered_file.relative_path, msg) for msg in parse_result.errors
                    )
                    # Still persist whatever was extracted before the error --
                    # partial results are better than discarding everything.

            file_id = store.upsert_file(
                path=discovered_file.relative_path,
                language=language,
                content_hash=new_hash,
                size_bytes=discovered_file.size_bytes,
            )
            store.replace_file_symbols(file_id, symbols)
            store.replace_file_relationships(file_id, relationships)
            store.replace_file_imports(file_id, imports)
            store.replace_file_chunks(
                file_id, discovered_file.relative_path, build_chunks(text, symbols)
            )
            result.files_indexed += 1

        known_paths = {f.path for f in store.list_files()}
        for stale_path in known_paths - discovered_paths:
            store.delete_file(stale_path)
            result.files_removed += 1
    finally:
        store.close()

    return result
