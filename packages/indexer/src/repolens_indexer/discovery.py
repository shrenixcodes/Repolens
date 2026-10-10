"""Repository file discovery with ignore-rule handling and path safety.

Walks a repository root and returns the set of files eligible for indexing.
Three layers of exclusion apply, in order:

1. A hard-coded secret-file pattern list (`HARD_EXCLUDED_PATTERNS`) that
   config cannot override -- it exists so a misconfigured `repolens.yaml`
   can never cause `.env` or private keys to be indexed.
2. `.gitignore` patterns from the repository root, when
   ``IndexingConfig.respect_gitignore`` is true.
3. User-configurable patterns from ``IndexingConfig.ignore``.

Every discovered path is validated with
:func:`repolens_shared.paths.resolve_within_root` before being returned, so a
symlink inside the repository that points outside of it can never leak a
file from elsewhere on disk into the index.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pathspec

from repolens_config.models import IndexingConfig
from repolens_shared.paths import is_within_root, safe_relative_path

HARD_EXCLUDED_PATTERNS: list[str] = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_rsa.*",
    "id_ed25519",
    "id_ed25519.*",
    "*.sqlite3",
    "*.sqlite3-journal",
    ".repolens/**",
]
"""Secret/runtime-data patterns excluded regardless of user configuration."""


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    """A file selected for indexing."""

    relative_path: str
    absolute_path: Path
    size_bytes: int


def _load_gitignore_spec(repo_root: Path) -> pathspec.PathSpec | None:
    gitignore = repo_root / ".gitignore"
    if not gitignore.is_file():
        return None
    lines = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
    return pathspec.PathSpec.from_lines("gitignore", lines)


def discover_files(repo_root: Path, config: IndexingConfig) -> list[DiscoveredFile]:
    """Return all files under ``repo_root`` eligible for indexing.

    Directories matched by an ignore pattern are pruned during the walk
    rather than filtered afterwards, so large ignored trees (``node_modules``,
    ``.git``) are never descended into.
    """
    repo_root = repo_root.resolve()

    hard_spec = pathspec.PathSpec.from_lines("gitignore", HARD_EXCLUDED_PATTERNS)
    user_spec = pathspec.PathSpec.from_lines("gitignore", config.ignore)
    gitignore_spec = _load_gitignore_spec(repo_root) if config.respect_gitignore else None

    def is_ignored(relative_posix: str, is_dir: bool) -> bool:
        candidates = [relative_posix, relative_posix + "/"] if is_dir else [relative_posix]
        for candidate in candidates:
            if hard_spec.match_file(candidate):
                return True
            if user_spec.match_file(candidate):
                return True
            if gitignore_spec is not None and gitignore_spec.match_file(candidate):
                return True
        return False

    discovered: list[DiscoveredFile] = []

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dir_path = Path(dirpath)

        kept_dirnames = []
        for dirname in dirnames:
            child = dir_path / dirname
            if not is_within_root(repo_root, child):
                continue  # symlinked directory escaping the repo root
            rel = safe_relative_path(repo_root, child)
            if is_ignored(rel, is_dir=True):
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in filenames:
            file_path = dir_path / filename
            if not is_within_root(repo_root, file_path):
                continue  # symlinked file escaping the repo root
            if file_path.is_symlink() and not file_path.resolve().is_file():
                continue
            rel = safe_relative_path(repo_root, file_path)
            if is_ignored(rel, is_dir=False):
                continue

            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                continue
            if size_bytes > config.max_file_size_bytes:
                continue

            discovered.append(
                DiscoveredFile(relative_path=rel, absolute_path=file_path, size_bytes=size_bytes)
            )

    discovered.sort(key=lambda f: f.relative_path)
    return discovered
