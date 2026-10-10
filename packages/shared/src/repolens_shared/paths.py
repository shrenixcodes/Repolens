"""Path-safety helpers.

Any time a path that originated outside of trusted, hard-coded source (a CLI
argument, an API request body, a value read from an indexed file, a symlink
target inside a scanned repository, ...) is used to touch the filesystem, it
must be passed through :func:`resolve_within_root` first. This is the single
choke point that prevents path-traversal escapes (`../../etc/passwd`,
absolute-path overrides, and symlink escapes) across the whole project.
"""

from __future__ import annotations

from pathlib import Path

from repolens_shared.exceptions import PathTraversalError


def resolve_within_root(root: Path, candidate: Path | str) -> Path:
    """Resolve ``candidate`` relative to ``root`` and guarantee it stays inside it.

    - Relative candidates are joined onto ``root``.
    - Absolute candidates are still required to land inside ``root`` once
      resolved (symlinks included) -- they are not treated as an escape hatch.
    - Both ``root`` and the result are fully resolved (``Path.resolve``) so
      that ``..`` segments and symlinks cannot be used to step outside.

    Raises:
        PathTraversalError: if the resolved path is not ``root`` itself or a
            descendant of it.
    """
    resolved_root = root.resolve()
    candidate_path = Path(candidate)

    joined = candidate_path if candidate_path.is_absolute() else resolved_root / candidate_path
    resolved_candidate = joined.resolve()

    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise PathTraversalError(
            f"Path '{candidate}' resolves outside of the allowed root '{root}'"
        ) from exc

    return resolved_candidate


def is_within_root(root: Path, candidate: Path | str) -> bool:
    """Non-raising variant of :func:`resolve_within_root`."""
    try:
        resolve_within_root(root, candidate)
    except PathTraversalError:
        return False
    return True


def safe_relative_path(root: Path, candidate: Path) -> str:
    """Return ``candidate``'s path relative to ``root`` using forward slashes.

    Raises PathTraversalError via :func:`resolve_within_root` if ``candidate``
    is not actually inside ``root``.
    """
    resolved = resolve_within_root(root, candidate)
    return resolved.relative_to(root.resolve()).as_posix()
