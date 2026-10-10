import subprocess
from pathlib import Path

import pytest


def _run(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _run(repo_root, "init", "-q", "-b", "main")
    _run(repo_root, "config", "user.name", "Test User")
    _run(repo_root, "config", "user.email", "test@example.com")

    (repo_root / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    _run(repo_root, "add", "a.py")
    _run(repo_root, "commit", "-q", "-m", "Add foo")

    (repo_root / "a.py").write_text("def foo():\n    return 2\n", encoding="utf-8")
    _run(repo_root, "add", "a.py")
    _run(repo_root, "commit", "-q", "-m", "Fix foo to return 2")

    return repo_root
