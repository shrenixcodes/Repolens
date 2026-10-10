"""File history, blame, and commit lookups."""

from __future__ import annotations

import re
from pathlib import Path

from repolens_git.models import BlameLine, Commit, FileChange
from repolens_git.runner import run_git
from repolens_shared.exceptions import GitError
from repolens_shared.paths import resolve_within_root, safe_relative_path

_FIELD_SEP = "\x1f"
_LOG_FORMAT = f"%H{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%aI{_FIELD_SEP}%s"

_STATUS_LABELS = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
}

_BLAME_HEADER_RE = re.compile(r"^[0-9a-f]{40} \d+ \d+(?: \d+)?$")


def _safe_relative(repo_root: Path, file_path: str) -> str:
    resolved = resolve_within_root(repo_root, file_path)
    return safe_relative_path(repo_root, resolved)


def _reject_flag_like(revision: str) -> None:
    """Raise if ``revision`` could be interpreted as a git option.

    A valid commit sha/ref never starts with "-"; refusing that shape
    before it reaches ``git show`` prevents argument injection from
    whatever supplied the revision string.
    """
    if not revision or revision.startswith("-"):
        raise GitError(f"Invalid revision: {revision!r}")


def _parse_log_line(line: str) -> Commit:
    sha, author_name, author_email, date, subject = line.split(_FIELD_SEP, 4)
    return Commit(
        sha=sha, author_name=author_name, author_email=author_email, date=date, subject=subject
    )


def file_history(repo_root: Path, file_path: str, *, limit: int = 20) -> list[Commit]:
    """Commits that touched ``file_path``, most recent first.

    Returns an empty list (not an error) for an untracked file or a path
    with no history -- that absence is itself meaningful information.
    """
    rel = _safe_relative(repo_root, file_path)
    output = run_git(
        repo_root,
        ["log", f"--format={_LOG_FORMAT}", "--follow", f"-n{limit}", "--", rel],
    )
    return [_parse_log_line(line) for line in output.splitlines() if line]


def commit_details(repo_root: Path, sha: str) -> Commit | None:
    try:
        # `git show <rev>` has no "--" form that keeps `<rev>` as a revision
        # (putting "--" before it reinterprets it as a pathspec instead), so
        # argument injection is prevented by rejecting flag-shaped input
        # up front instead.
        _reject_flag_like(sha)
        output = run_git(repo_root, ["show", "-s", f"--format={_LOG_FORMAT}", sha])
    except GitError:
        return None
    lines = [line for line in output.splitlines() if line]
    return _parse_log_line(lines[0]) if lines else None


def changed_files_in_commit(repo_root: Path, sha: str) -> list[FileChange]:
    try:
        _reject_flag_like(sha)
        output = run_git(repo_root, ["show", "--name-status", "--format=", sha])
    except GitError:
        return []
    changes = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        changes.append(FileChange(path=path, change_type=_STATUS_LABELS.get(status[0], status)))
    return changes


def blame(repo_root: Path, file_path: str) -> list[BlameLine]:
    """Per-line authorship for ``file_path`` at the current revision."""
    rel = _safe_relative(repo_root, file_path)
    try:
        output = run_git(repo_root, ["blame", "--line-porcelain", "--", rel])
    except GitError:
        return []

    lines: list[BlameLine] = []
    sha = author_name = author_date = summary = ""
    line_number = 0

    for raw_line in output.splitlines():
        if _BLAME_HEADER_RE.match(raw_line):
            parts = raw_line.split()
            sha = parts[0]
            line_number = int(parts[2])
        elif raw_line.startswith("author "):
            author_name = raw_line[len("author ") :]
        elif raw_line.startswith("author-time "):
            author_date = raw_line[len("author-time ") :]
        elif raw_line.startswith("summary "):
            summary = raw_line[len("summary ") :]
        elif raw_line.startswith("\t"):
            lines.append(
                BlameLine(
                    line_number=line_number,
                    sha=sha,
                    author_name=author_name,
                    author_date=author_date,
                    summary=summary,
                    content=raw_line[1:],
                )
            )

    return lines
