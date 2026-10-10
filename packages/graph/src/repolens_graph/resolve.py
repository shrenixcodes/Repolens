"""Best-effort cross-file resolution of parser-recorded relationships.

See the package README for the resolution policy. Everything here is a pure
function over in-memory data (file path sets, name indexes) -- no
filesystem or network access -- so a relationship either resolves against
files RepoLens actually indexed, or it doesn't resolve at all.
"""

from __future__ import annotations

import posixpath

_PY_EXTENSION = ".py"
_JS_TS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")


def resolve_python_import(importing_path: str, module: str, known_paths: frozenset[str]) -> str | None:
    """Resolve a Python import's module string to a file in ``known_paths``.

    ``module`` is the parser's ``ParsedImport.module`` -- leading dots
    encode relativity (``.utils`` is one level relative, ``..pkg.mod`` is
    two). Absolute (non-relative) imports are resolved as dotted paths from
    the repository root.
    """
    level = len(module) - len(module.lstrip("."))
    remainder = module[level:]
    parts = remainder.split(".") if remainder else []

    if level == 0:
        base_dir = ""
    else:
        importing_dir = posixpath.dirname(importing_path)
        # `from . import x` (level 1) resolves relative to the importing
        # file's own package directory; each extra dot goes up one more.
        base_dir = importing_dir
        for _ in range(level - 1):
            base_dir = posixpath.dirname(base_dir)

    candidate_base = posixpath.normpath(posixpath.join(base_dir, *parts)) if parts else base_dir
    candidate_base = candidate_base if candidate_base != "." else ""

    for candidate in (
        f"{candidate_base}{_PY_EXTENSION}",
        posixpath.join(candidate_base, f"__init__{_PY_EXTENSION}"),
    ):
        normalized = posixpath.normpath(candidate)
        if normalized in known_paths:
            return normalized
    return None


def resolve_js_import(importing_path: str, module: str, known_paths: frozenset[str]) -> str | None:
    """Resolve a relative JS/TS import specifier to a file in ``known_paths``.

    Bare (non-relative) specifiers (``react``, ``lodash/debounce``) are
    assumed to be external packages and are never resolved.
    """
    if not module.startswith("."):
        return None

    importing_dir = posixpath.dirname(importing_path)
    candidate_base = posixpath.normpath(posixpath.join(importing_dir, module))

    candidates = [candidate_base]
    candidates += [f"{candidate_base}{ext}" for ext in _JS_TS_EXTENSIONS]
    candidates += [posixpath.join(candidate_base, f"index{ext}") for ext in _JS_TS_EXTENSIONS]

    for candidate in candidates:
        if candidate in known_paths:
            return candidate
    return None


class SymbolNameIndex:
    """Maps a bare symbol name to every (path, qualified_name, kind) sharing it.

    Used to resolve `calls`/`inherits`/`implements` relationships: a name
    resolves only when it is unambiguous across the whole repository.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, list[tuple[str, str, str]]] = {}

    def add(self, name: str, path: str, qualified_name: str, kind: str) -> None:
        self._by_name.setdefault(name, []).append((path, qualified_name, kind))

    def resolve_unambiguous(self, name: str) -> tuple[str, str, str] | None:
        candidates = self._by_name.get(name, [])
        if len(candidates) == 1:
            return candidates[0]
        return None
