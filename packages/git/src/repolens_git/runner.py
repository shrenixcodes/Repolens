"""Safe subprocess execution of the local `git` binary."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from repolens_shared.exceptions import GitError


def is_git_repository(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def run_git(repo_root: Path, args: list[str], *, timeout: float = 15.0) -> str:
    """Run ``git`` with ``args`` inside ``repo_root``.

    Always invoked as an explicit argument list (never ``shell=True``), so
    nothing in ``args`` -- including file paths or branch names -- can be
    interpreted as shell syntax.
    """
    git_path = shutil.which("git")
    if git_path is None:
        raise GitError("git executable not found on PATH")
    if not is_git_repository(repo_root):
        raise GitError(f"{repo_root} is not a Git repository")

    try:
        result = subprocess.run(  # noqa: S603 -- fixed executable, explicit args, no shell
            [git_path, "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git {' '.join(args)} timed out after {timeout}s") from exc
    except OSError as exc:
        raise GitError(f"failed to run git: {exc}") from exc

    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")

    return result.stdout
