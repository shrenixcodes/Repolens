from pathlib import Path

from repolens_config.models import IndexingConfig, RepoLensConfig
from repolens_indexer.db import IndexStore
from repolens_indexer.embeddings import cosine_similarity, semantic_search
from repolens_indexer.pipeline import EmbeddingBackend, index_db_path, run_index


def test_cosine_similarity_identical_vectors_is_one() -> None:
    assert abs(cosine_similarity([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal_vectors_is_zero() -> None:
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_similarity_zero_vector_is_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


def _fake_embed_batch(texts: list[str]) -> list[list[float]]:
    # One-hot-ish deterministic vector keyed by text length, just so distinct
    # chunk contents land at distinguishable points for the test to assert on.
    return [[float(len(t) % 7), float(len(t) % 5), 1.0] for t in texts]


def test_pipeline_generates_and_stores_embeddings_when_enabled(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    config = RepoLensConfig(indexing=IndexingConfig(enable_embeddings=True))
    backend = EmbeddingBackend(provider="mock", model="test-model", embed_batch=_fake_embed_batch)

    run_index(tmp_path, config, embedding_backend=backend)

    store = IndexStore.open(index_db_path(tmp_path, config))
    rows = store.iter_embeddings(provider="mock", model="test-model")
    assert len(rows) == 1
    assert rows[0].symbol_qualified_name == "foo"


def test_pipeline_skips_embeddings_when_disabled(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    config = RepoLensConfig()  # enable_embeddings defaults to False
    backend = EmbeddingBackend(provider="mock", model="test-model", embed_batch=_fake_embed_batch)

    run_index(tmp_path, config, embedding_backend=backend)

    store = IndexStore.open(index_db_path(tmp_path, config))
    assert store.iter_embeddings(provider="mock", model="test-model") == []


def test_semantic_search_ranks_closer_vector_first(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text(
        "def a_much_longer_function_name_here():\n    return 2\n", encoding="utf-8"
    )
    config = RepoLensConfig(indexing=IndexingConfig(enable_embeddings=True))
    backend = EmbeddingBackend(provider="mock", model="test-model", embed_batch=_fake_embed_batch)
    run_index(tmp_path, config, embedding_backend=backend)

    store = IndexStore.open(index_db_path(tmp_path, config))
    query_vector = _fake_embed_batch(["def foo():\n    return 1"])[0]
    results = semantic_search(store, query_vector, provider="mock", model="test-model")
    assert results
    assert results[0].file_path == "a.py"


def test_embedding_failure_is_recorded_but_does_not_abort_indexing(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    config = RepoLensConfig(indexing=IndexingConfig(enable_embeddings=True))

    def _failing_embed(texts: list[str]) -> list[list[float]]:
        raise RuntimeError("provider unreachable")

    backend = EmbeddingBackend(provider="mock", model="test-model", embed_batch=_failing_embed)
    result = run_index(tmp_path, config, embedding_backend=backend)

    assert result.files_indexed == 1
    assert any("embedding generation failed" in msg for _, msg in result.errors)

    store = IndexStore.open(index_db_path(tmp_path, config))
    assert store.get_file("a.py") is not None
