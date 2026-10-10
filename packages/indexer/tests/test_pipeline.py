from pathlib import Path

import pytest

from repolens_config.models import DatabaseConfig, RepoLensConfig
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import index_db_path, run_index
from repolens_indexer.status import get_status
from repolens_shared.exceptions import PathTraversalError


def _write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_indexes_python_and_js_files(tmp_path: Path) -> None:
    _write(tmp_path, "app/utils.py", "def helper():\n    return 1\n")
    _write(tmp_path, "app/widget.js", "function widget() { return 1; }\n")
    _write(tmp_path, "README.md", "# hello\n")

    config = RepoLensConfig()
    result = run_index(tmp_path, config)

    assert result.files_scanned == 3
    assert result.files_indexed == 3
    assert result.files_failed == 0

    store = IndexStore.open(index_db_path(tmp_path, config))
    paths = {f.path for f in store.list_files()}
    assert paths == {"app/utils.py", "app/widget.js", "README.md"}
    readme = store.get_file("README.md")
    assert readme is not None
    assert readme.language is None  # no parser for markdown -- honestly reported


def test_second_run_skips_unchanged_files(tmp_path: Path) -> None:
    _write(tmp_path, "app.py", "def f():\n    return 1\n")
    config = RepoLensConfig()

    first = run_index(tmp_path, config)
    assert first.files_indexed == 1

    second = run_index(tmp_path, config)
    assert second.files_indexed == 0
    assert second.files_unchanged == 1


def test_changed_file_is_reindexed(tmp_path: Path) -> None:
    path = _write(tmp_path, "app.py", "def f():\n    return 1\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)

    path.write_text("def f():\n    return 2\n\ndef g():\n    return 3\n", encoding="utf-8")
    result = run_index(tmp_path, config)
    assert result.files_indexed == 1
    assert result.files_unchanged == 0

    store = IndexStore.open(index_db_path(tmp_path, config))
    file_row = store.get_file("app.py")
    symbols = {s.name for s in store.list_symbols_for_file(file_row.id)}
    assert symbols == {"f", "g"}


def test_removed_file_is_deleted_from_index(tmp_path: Path) -> None:
    path = _write(tmp_path, "app.py", "def f():\n    return 1\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)

    path.unlink()
    result = run_index(tmp_path, config)
    assert result.files_removed == 1

    store = IndexStore.open(index_db_path(tmp_path, config))
    assert store.get_file("app.py") is None


def test_syntax_error_file_is_counted_as_failed_but_still_indexed(tmp_path: Path) -> None:
    _write(tmp_path, "broken.py", "def f(:\n  pass")
    config = RepoLensConfig()
    result = run_index(tmp_path, config)

    assert result.files_failed == 1
    assert result.errors

    store = IndexStore.open(index_db_path(tmp_path, config))
    assert store.get_file("broken.py") is not None


def test_status_reports_counts(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "class Foo:\n    def bar(self):\n        pass\n")
    _write(tmp_path, "b.py", "from .a import Foo\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)

    store = IndexStore.open(index_db_path(tmp_path, config))
    status = get_status(store)
    assert status.total_files == 2
    assert status.total_symbols >= 2  # Foo class + bar method
    assert status.files_by_language.get("python") == 2
    assert status.last_indexed_at is not None


def test_index_db_path_rejects_traversal_via_malicious_config(tmp_path: Path) -> None:
    # A repolens.yaml committed to an untrusted repository could try to
    # point database.path outside the repo -- this must never be honored.
    config = RepoLensConfig(database=DatabaseConfig(path="../../../../tmp/evil.sqlite3"))
    with pytest.raises(PathTraversalError):
        index_db_path(tmp_path, config)
