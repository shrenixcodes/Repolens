from pathlib import Path

import pytest

from repolens_config.models import IndexingConfig
from repolens_indexer.discovery import discover_files


def _write(root: Path, rel: str, content: str = "x") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_discovers_plain_source_files(tmp_path: Path) -> None:
    _write(tmp_path, "src/app.py", "print('hi')")
    _write(tmp_path, "README.md", "# hi")

    found = {f.relative_path for f in discover_files(tmp_path, IndexingConfig())}
    assert found == {"src/app.py", "README.md"}


def test_prunes_default_ignored_directories(tmp_path: Path) -> None:
    _write(tmp_path, "src/app.py")
    _write(tmp_path, "node_modules/pkg/index.js")
    _write(tmp_path, ".git/HEAD")
    _write(tmp_path, "__pycache__/app.cpython-313.pyc")

    found = {f.relative_path for f in discover_files(tmp_path, IndexingConfig())}
    assert found == {"src/app.py"}


def test_hard_excludes_secret_files_even_if_user_tries_to_allow_them(tmp_path: Path) -> None:
    _write(tmp_path, ".env", "SECRET=1")
    _write(tmp_path, "id_rsa", "fake-key")
    _write(tmp_path, "src/app.py")

    # A user cannot un-ignore secret patterns by passing an empty ignore list.
    config = IndexingConfig(ignore=[], respect_gitignore=False)
    found = {f.relative_path for f in discover_files(tmp_path, config)}
    assert found == {"src/app.py"}


def test_respects_project_gitignore(tmp_path: Path) -> None:
    _write(tmp_path, "src/app.py")
    _write(tmp_path, "build/output.js")
    _write(tmp_path, ".gitignore", "build/\n")

    found = {f.relative_path for f in discover_files(tmp_path, IndexingConfig())}
    assert "build/output.js" not in found
    assert "src/app.py" in found


def test_can_disable_gitignore_respecting(tmp_path: Path) -> None:
    _write(tmp_path, "scratch/notes.txt")
    _write(tmp_path, ".gitignore", "scratch/\n")

    config = IndexingConfig(respect_gitignore=False, ignore=[])
    found = {f.relative_path for f in discover_files(tmp_path, config)}
    assert "scratch/notes.txt" in found


def test_skips_files_over_max_size(tmp_path: Path) -> None:
    _write(tmp_path, "big.txt", "x" * 100)
    _write(tmp_path, "small.txt", "x")

    config = IndexingConfig(max_file_size_bytes=10)
    found = {f.relative_path for f in discover_files(tmp_path, config)}
    assert found == {"small.txt"}


def test_user_ignore_patterns_are_applied(tmp_path: Path) -> None:
    _write(tmp_path, "src/app.py")
    _write(tmp_path, "docs/notes.md")

    config = IndexingConfig(ignore=["docs"])
    found = {f.relative_path for f in discover_files(tmp_path, config)}
    assert found == {"src/app.py"}


def test_symlinked_directory_escaping_root_is_not_followed(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write(repo_root, "src/app.py")

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("leak me", encoding="utf-8")

    link = repo_root / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not supported in this environment")

    found = {f.relative_path for f in discover_files(repo_root, IndexingConfig())}
    assert found == {"src/app.py"}
