"""Environment diagnostics for `repolens doctor`.

Each check is self-contained and never raises -- a broken check reports
itself as a failure rather than crashing the whole command, since the point
of `doctor` is to work even when the environment is unhealthy.
"""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Status = Literal["ok", "warn", "fail"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    status: Status
    detail: str
    fix_hint: str | None = None


def _check_python() -> CheckResult:
    version = sys.version_info
    detail = f"Python {version.major}.{version.minor}.{version.micro}"
    if version < (3, 10):
        return CheckResult(
            "python",
            "fail",
            detail,
            "RepoLens requires Python 3.10 or newer.",
        )
    return CheckResult("python", "ok", detail)


def _check_git() -> CheckResult:
    git_path = shutil.which("git")
    if git_path is None:
        return CheckResult(
            "git",
            "warn",
            "git executable not found on PATH",
            "Install Git to enable repository history and blame features.",
        )
    try:
        result = subprocess.run(  # noqa: S603 -- fixed args, no shell, no user input
            [git_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except OSError as exc:
        return CheckResult("git", "fail", f"git found but failed to run: {exc}")
    return CheckResult("git", "ok", result.stdout.strip() or "git available")


def _check_sqlite() -> CheckResult:
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("SELECT 1")
        conn.close()
    except sqlite3.Error as exc:
        return CheckResult("sqlite", "fail", f"sqlite3 module unusable: {exc}")
    return CheckResult("sqlite", "ok", f"sqlite3 module OK (sqlite {sqlite3.sqlite_version})")


def _check_cache_dir(repo_root: Path) -> CheckResult:
    cache_dir = repo_root / ".repolens"
    try:
        cache_dir.mkdir(exist_ok=True)
        probe = cache_dir / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return CheckResult(
            "cache_dir",
            "fail",
            f"cannot write to {cache_dir}: {exc}",
            "Check filesystem permissions for the repository directory.",
        )
    return CheckResult("cache_dir", "ok", f"{cache_dir} is writable")


def _check_config(repo_root: Path) -> CheckResult:
    try:
        from repolens_config import load_config

        config = load_config(repo_root)
    except Exception as exc:  # defensive: doctor must never crash on bad config
        return CheckResult(
            "config",
            "fail",
            f"configuration failed to load: {exc}",
            "Check repolens.yaml for syntax errors.",
        )
    return CheckResult(
        "config",
        "ok",
        f"llm provider={config.llm.provider}, embedding provider={config.embedding.provider}",
    )


def run_checks(repo_root: Path) -> list[CheckResult]:
    return [
        _check_python(),
        _check_git(),
        _check_sqlite(),
        _check_cache_dir(repo_root),
        _check_config(repo_root),
    ]
