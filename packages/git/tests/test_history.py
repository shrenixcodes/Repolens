from pathlib import Path

import pytest

from repolens_git.history import blame, changed_files_in_commit, commit_details, file_history
from repolens_git.runner import is_git_repository
from repolens_shared.exceptions import GitError, PathTraversalError


def test_is_git_repository(tmp_path: Path, git_repo: Path) -> None:
    assert is_git_repository(git_repo) is True
    assert is_git_repository(tmp_path) is False


def test_file_history_most_recent_first(git_repo: Path) -> None:
    commits = file_history(git_repo, "a.py")
    assert len(commits) == 2
    assert commits[0].subject == "Fix foo to return 2"
    assert commits[1].subject == "Add foo"
    assert commits[0].author_name == "Test User"


def test_file_history_respects_limit(git_repo: Path) -> None:
    commits = file_history(git_repo, "a.py", limit=1)
    assert len(commits) == 1
    assert commits[0].subject == "Fix foo to return 2"


def test_file_history_empty_for_untracked_file(git_repo: Path) -> None:
    assert file_history(git_repo, "never_existed.py") == []


def test_file_history_rejects_path_outside_repo(git_repo: Path) -> None:
    with pytest.raises(PathTraversalError):
        file_history(git_repo, "../outside.py")


def test_file_history_raises_for_non_git_directory(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    with pytest.raises(GitError):
        file_history(tmp_path, "a.py")


def test_commit_details_returns_commit(git_repo: Path) -> None:
    commits = file_history(git_repo, "a.py")
    detail = commit_details(git_repo, commits[0].sha)
    assert detail is not None
    assert detail.subject == "Fix foo to return 2"


def test_commit_details_returns_none_for_unknown_sha(git_repo: Path) -> None:
    assert commit_details(git_repo, "0" * 40) is None


def test_changed_files_in_commit(git_repo: Path) -> None:
    commits = file_history(git_repo, "a.py")
    changes = changed_files_in_commit(git_repo, commits[-1].sha)
    assert len(changes) == 1


def test_commit_details_rejects_flag_like_revision(git_repo: Path) -> None:
    assert commit_details(git_repo, "--upload-pack=/bin/sh") is None


def test_changed_files_in_commit_rejects_flag_like_revision(git_repo: Path) -> None:
    assert changed_files_in_commit(git_repo, "--output=/tmp/pwned") == []


def test_blame_attributes_lines_to_commits(git_repo: Path) -> None:
    lines = blame(git_repo, "a.py")
    assert len(lines) == 2
    assert lines[0].content == "def foo():"
    assert lines[1].content == "    return 2"
    assert all(line.author_name == "Test User" for line in lines)


def test_blame_empty_for_untracked_file(git_repo: Path) -> None:
    assert blame(git_repo, "never_existed.py") == []
