"""Git data types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Commit:
    sha: str
    author_name: str
    author_email: str
    date: str
    """ISO-8601 commit date, as reported by git (author date)."""
    subject: str


@dataclass(frozen=True, slots=True)
class FileChange:
    path: str
    change_type: str
    """git's single-letter status code: A (added), M (modified), D (deleted), R (renamed), ..."""


@dataclass(frozen=True, slots=True)
class BlameLine:
    line_number: int
    sha: str
    author_name: str
    author_date: str
    summary: str
    content: str
