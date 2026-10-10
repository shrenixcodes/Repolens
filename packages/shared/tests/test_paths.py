from pathlib import Path

import pytest

from repolens_shared.exceptions import PathTraversalError
from repolens_shared.paths import is_within_root, resolve_within_root, safe_relative_path


def test_resolve_within_root_allows_relative_descendant(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    result = resolve_within_root(tmp_path, "src/app.py")
    assert result == (tmp_path / "src" / "app.py").resolve()


def test_resolve_within_root_rejects_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathTraversalError):
        resolve_within_root(tmp_path, "../../etc/passwd")


def test_resolve_within_root_rejects_absolute_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(PathTraversalError):
        resolve_within_root(tmp_path, outside)


def test_resolve_within_root_rejects_symlink_escape(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside_target = tmp_path / "secret.txt"
    outside_target.write_text("top secret")

    link = repo_root / "escape_link"
    try:
        link.symlink_to(outside_target)
    except OSError:
        pytest.skip("symlinks not supported in this environment")

    with pytest.raises(PathTraversalError):
        resolve_within_root(repo_root, "escape_link")


def test_is_within_root_does_not_raise(tmp_path: Path) -> None:
    assert is_within_root(tmp_path, "ok.txt") is True
    assert is_within_root(tmp_path, "../escape.txt") is False


def test_safe_relative_path_uses_forward_slashes(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    rel = safe_relative_path(tmp_path, nested / "file.py")
    assert rel == "a/b/file.py"
