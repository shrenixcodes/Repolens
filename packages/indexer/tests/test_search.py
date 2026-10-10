from pathlib import Path

from repolens_config.models import RepoLensConfig
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import index_db_path, run_index
from repolens_indexer.search import search_lexical


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_search_finds_function_by_name(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/auth.py",
        "def verify_jwt_token(token):\n    return decode(token)\n",
    )
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = search_lexical(store, "jwt token")
    assert any(r.symbol_qualified_name == "verify_jwt_token" for r in results)
    assert results[0].file_path == "app/auth.py"


def test_search_ranks_more_relevant_match_first(tmp_path: Path) -> None:
    _write(tmp_path, "payments.py", "def charge_card():\n    '''Process a payment charge.'''\n    pass\n")
    _write(tmp_path, "unrelated.py", "def other():\n    pass\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = search_lexical(store, "payment charge")
    assert results
    assert results[0].file_path == "payments.py"


def test_search_returns_empty_for_empty_query(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def foo():\n    pass\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    assert search_lexical(store, "") == []
    assert search_lexical(store, "!!!") == []


def test_search_handles_punctuation_in_query_without_crashing(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def foo():\n    pass\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    # FTS5 special characters -- must not raise.
    results = search_lexical(store, 'foo() OR "bar" NEAR/2')
    assert isinstance(results, list)


def test_search_respects_limit(tmp_path: Path) -> None:
    for i in range(5):
        _write(tmp_path, f"m{i}.py", f"def shared_name_{i}():\n    '''shared docstring token.'''\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = search_lexical(store, "shared docstring", limit=2)
    assert len(results) <= 2


def test_reindexing_file_updates_search_results(tmp_path: Path) -> None:
    path = tmp_path / "a.py"
    path.write_text("def old_name():\n    pass\n", encoding="utf-8")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))
    assert any(r.symbol_qualified_name == "old_name" for r in search_lexical(store, "old_name"))

    path.write_text("def new_name():\n    pass\n", encoding="utf-8")
    run_index(tmp_path, config)
    store2 = IndexStore.open(index_db_path(tmp_path, config))
    results = search_lexical(store2, "old_name")
    assert not any(r.symbol_qualified_name == "old_name" for r in results)
