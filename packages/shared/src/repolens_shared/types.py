"""Small, dependency-free value types shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """A precise, citable location inside a repository.

    ``path`` is always repository-relative (forward slashes), never absolute
    -- absolute paths would leak local filesystem layout into answers, API
    responses, and persisted data.
    """

    path: str
    start_line: int
    end_line: int

    def __str__(self) -> str:
        if self.start_line == self.end_line:
            return f"{self.path}:{self.start_line}"
        return f"{self.path}:{self.start_line}-{self.end_line}"


@dataclass(frozen=True, slots=True)
class Citation:
    """A piece of evidence backing a generated answer.

    ``excerpt`` should be short (a signature or a few lines), never a full
    file dump -- citations point the reader at the source, they don't
    replace reading it.
    """

    location: SourceLocation
    symbol_name: str | None = None
    excerpt: str | None = None
