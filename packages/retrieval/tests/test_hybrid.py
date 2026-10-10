from pathlib import Path

from repolens_config.models import IndexingConfig, RepoLensConfig
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import EmbeddingBackend, index_db_path, run_index
from repolens_retrieval.hybrid import hybrid_search


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_hybrid_search_lexical_only_when_no_embed_fn(tmp_path: Path) -> None:
    _write(tmp_path, "auth.py", "def verify_jwt_token(token):\n    return True\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = hybrid_search(store, "jwt token")
    assert results
    assert results[0].file_path == "auth.py"
    assert results[0].sources == ("lexical",)


def test_structural_boost_for_exact_symbol_name(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "a.py",
        "def process_payment():\n    '''Handles payment processing logic.'''\n    pass\n",
    )
    _write(
        tmp_path,
        "b.py",
        "def unrelated():\n    '''Talks about payment processing in a comment.'''\n    pass\n",
    )
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = hybrid_search(store, "process_payment")
    assert results[0].symbol_qualified_name == "process_payment"
    assert "structural" in results[0].sources


def test_hybrid_search_combines_lexical_and_semantic(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def login():\n    return 1\n")

    def fake_embed(text: str) -> list[float]:
        return [float(len(text) % 3), 1.0]

    config = RepoLensConfig(indexing=IndexingConfig(enable_embeddings=True))
    backend = EmbeddingBackend(
        provider="mock", model="test", embed_batch=lambda texts: [fake_embed(t) for t in texts]
    )
    run_index(tmp_path, config, embedding_backend=backend)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = hybrid_search(
        store, "login", embed_fn=fake_embed, embedding_provider="mock", embedding_model="test"
    )
    assert results
    assert "semantic" in results[0].sources or "lexical" in results[0].sources


def test_empty_repository_returns_no_results(tmp_path: Path) -> None:
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))
    assert hybrid_search(store, "anything") == []


def test_respects_limit(tmp_path: Path) -> None:
    for i in range(5):
        _write(tmp_path, f"m{i}.py", f"def shared_token_{i}():\n    '''shared token word.'''\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))

    results = hybrid_search(store, "shared token", limit=2)
    assert len(results) <= 2
