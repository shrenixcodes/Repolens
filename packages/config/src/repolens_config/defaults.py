"""Default values shared between the config models and documentation."""

from __future__ import annotations

DEFAULT_IGNORE_PATTERNS: list[str] = [
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "coverage",
    ".next",
    "target",
    "vendor",
    ".repolens",
    "*.min.js",
    "*.map",
    "*.lock",
    "*.pyc",
    "*.pyo",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.sqlite3",
]
"""Directories/globs excluded from indexing by default.

Covers generated output, dependency directories, virtual environments, and
common secret-shaped files (`.env`, private keys). Users can extend this
list via `indexing.ignore` in `repolens.yaml`; they cannot shrink the
built-in secret-file patterns from the config file alone (see
`repolens_indexer.discovery` for the hard-excluded secret patterns).
"""

DEFAULT_MAX_FILE_SIZE_BYTES = 1_000_000
"""Files larger than this are skipped during indexing (likely generated/binary)."""
