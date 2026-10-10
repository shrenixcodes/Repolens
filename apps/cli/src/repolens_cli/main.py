"""The `repolens` CLI entry point."""

from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

import click

from repolens_cli.doctor import run_checks
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


if __name__ == "__main__":
    cli()
