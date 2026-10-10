"""The `repolens` CLI entry point."""

from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

import click
import yaml

from repolens_cli.doctor import run_checks
from repolens_config import load_config
from repolens_indexer import get_status, index_db_path, run_index, search_lexical
from repolens_indexer.db import IndexStore
from repolens_shared.logging import configure_logging

try:
    __version__ = metadata.version("repolens-cli")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+dev"

_STATUS_SYMBOL = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]"}


@click.group()
@click.version_option(__version__, prog_name="repolens")
def cli() -> None:
    """RepoLens -- local-first AI codebase intelligence."""
    configure_logging()


@cli.command()
@click.option(
    "--repo",
    "repo_path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    show_default="current directory",
    help="Repository to diagnose.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def doctor(repo_path: Path, as_json: bool) -> None:
    """Check that the local environment is ready to run RepoLens."""
    results = run_checks(repo_path.resolve())

    if as_json:
        click.echo(
            json.dumps(
                [
                    {
                        "name": r.name,
                        "status": r.status,
                        "detail": r.detail,
                        "fix_hint": r.fix_hint,
                    }
                    for r in results
                ],
                indent=2,
            )
        )
    else:
        click.echo("RepoLens environment check")
        click.echo("---------------------------")
        for r in results:
            click.echo(f"{_STATUS_SYMBOL[r.status]} {r.name}: {r.detail}")
            if r.status != "ok" and r.fix_hint:
                click.echo(f"       -> {r.fix_hint}")

    if any(r.status == "fail" for r in results):
        raise SystemExit(1)


_REPO_OPTION = click.option(
    "--repo",
    "repo_path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    show_default="current directory",
    help="Repository to operate on.",
)


@cli.command()
@_REPO_OPTION
def init(repo_path: Path) -> None:
    """Create a repolens.yaml with default, fully-offline settings."""
    repo_path = repo_path.resolve()
    config_path = repo_path / "repolens.yaml"
    if config_path.exists():
        click.echo(f"{config_path} already exists -- leaving it untouched.")
        return

    config = load_config(repo_path, env={})
    config_path.write_text(
        yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8"
    )
    (repo_path / ".repolens").mkdir(exist_ok=True)
    click.echo(f"Wrote {config_path}")
    click.echo("Run 'repolens index' next.")


@cli.command()
@_REPO_OPTION
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def index(repo_path: Path, as_json: bool) -> None:
    """Scan the repository and (re)build its local index."""
    repo_path = repo_path.resolve()
    config = load_config(repo_path)

    embedding_backend = None
    if config.indexing.enable_embeddings:
        from repolens_ai import build_embedding_provider
        from repolens_indexer import EmbeddingBackend

        provider = build_embedding_provider(config.embedding)
        embedding_backend = EmbeddingBackend(
            provider=provider.name, model=provider.model, embed_batch=provider.embed_batch
        )

    result = run_index(repo_path, config, embedding_backend=embedding_backend)

    if as_json:
        click.echo(
            json.dumps(
                {
                    "files_scanned": result.files_scanned,
                    "files_indexed": result.files_indexed,
                    "files_unchanged": result.files_unchanged,
                    "files_removed": result.files_removed,
                    "files_failed": result.files_failed,
                    "errors": [{"path": p, "message": m} for p, m in result.errors],
                },
                indent=2,
            )
        )
    else:
        click.echo(
            f"Scanned {result.files_scanned} files: "
            f"{result.files_indexed} indexed, {result.files_unchanged} unchanged, "
            f"{result.files_removed} removed, {result.files_failed} failed."
        )
        for path, message in result.errors:
            click.echo(f"  [WARN] {path}: {message}")

    if result.files_failed:
        raise SystemExit(1)


@cli.command()
@_REPO_OPTION
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def status(repo_path: Path, as_json: bool) -> None:
    """Show statistics about the repository's current index."""
    repo_path = repo_path.resolve()
    config = load_config(repo_path)
    db_path = index_db_path(repo_path, config)
    if not db_path.exists():
        click.echo("This repository has not been indexed yet. Run 'repolens index' first.")
        raise SystemExit(1)

    store = IndexStore.open(db_path)
    try:
        s = get_status(store)
    finally:
        store.close()

    if as_json:
        click.echo(
            json.dumps(
                {
                    "total_files": s.total_files,
                    "total_symbols": s.total_symbols,
                    "total_relationships": s.total_relationships,
                    "resolved_relationships": s.resolved_relationships,
                    "files_by_language": s.files_by_language,
                    "symbols_by_kind": s.symbols_by_kind,
                    "last_indexed_at": s.last_indexed_at,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Files:          {s.total_files}")
        click.echo(f"Symbols:        {s.total_symbols}")
        click.echo(
            f"Relationships:  {s.total_relationships} ({s.resolved_relationships} resolved)"
        )
        click.echo(f"Last indexed:   {s.last_indexed_at}")
        click.echo("Languages:")
        for language, count in sorted(s.files_by_language.items()):
            click.echo(f"  {language}: {count} files")


@cli.command()
@click.argument("query")
@_REPO_OPTION
@click.option("--limit", default=10, show_default=True, help="Maximum number of results.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def search(query: str, repo_path: Path, limit: int, as_json: bool) -> None:
    """Lexically search the repository's indexed source for QUERY."""
    repo_path = repo_path.resolve()
    config = load_config(repo_path)
    db_path = index_db_path(repo_path, config)
    if not db_path.exists():
        click.echo("This repository has not been indexed yet. Run 'repolens index' first.")
        raise SystemExit(1)

    store = IndexStore.open(db_path)
    try:
        results = search_lexical(store, query, limit=limit)
    finally:
        store.close()

    if as_json:
        click.echo(
            json.dumps(
                [
                    {
                        "file_path": r.file_path,
                        "symbol": r.symbol_qualified_name,
                        "start_line": r.start_line,
                        "end_line": r.end_line,
                        "score": r.score,
                        "snippet": r.snippet,
                    }
                    for r in results
                ],
                indent=2,
            )
        )
        return

    if not results:
        click.echo("No matches found.")
        return

    for r in results:
        location = f"{r.file_path}:{r.start_line}-{r.end_line}"
        symbol_suffix = f" ({r.symbol_qualified_name})" if r.symbol_qualified_name else ""
        click.echo(f"{location}{symbol_suffix}")
        for line in r.snippet.splitlines()[:3]:
            click.echo(f"    {line}")
        click.echo("")


if __name__ == "__main__":
    cli()
