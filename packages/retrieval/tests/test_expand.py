from pathlib import Path

from repolens_config.models import RepoLensConfig
from repolens_graph.builder import build_graph
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import index_db_path, run_index
from repolens_retrieval.expand import expand_with_graph
from repolens_retrieval.models import RetrievedChunk


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_expand_pulls_in_callee(tmp_path: Path) -> None:
    _write(tmp_path, "utils.py", "def helper():\n    return 1\n")
    _write(tmp_path, "service.py", "from .utils import helper\n\ndef login():\n    return helper()\n")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))
    repo_graph = build_graph(store)

    seed = [
        RetrievedChunk(
            file_path="service.py",
            symbol_qualified_name="login",
            start_line=3,
            end_line=4,
            content="def login(): ...",
            score=1.0,
            sources=("lexical",),
        )
    ]
    related = expand_with_graph(repo_graph, seed)
    assert any(r.qualified_name == "helper" and r.relation == "calls" for r in related)


def test_expand_skips_chunks_without_symbol(tmp_path: Path) -> None:
    _write(tmp_path, "README.md", "just text, no symbols")
    config = RepoLensConfig()
    run_index(tmp_path, config)
    store = IndexStore.open(index_db_path(tmp_path, config))
    repo_graph = build_graph(store)

    seed = [
        RetrievedChunk(
            file_path="README.md",
            symbol_qualified_name=None,
            start_line=1,
            end_line=1,
            content="just text",
            score=1.0,
            sources=("lexical",),
        )
    ]
    assert expand_with_graph(repo_graph, seed) == []
