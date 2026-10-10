from pathlib import Path

from repolens_graph.builder import build_graph
from repolens_graph.ids import file_node_id, symbol_node_id
from repolens_graph.queries import (
    dependencies_of,
    dependents_of,
    transitive_dependents,
)
from repolens_graph.stats import important_files
from repolens_indexer.db import IndexStore
from repolens_parser.python_parser import PythonParser
from repolens_shared.hashing import text_hash


def _index_python_files(tmp_path: Path, files: dict[str, str]) -> IndexStore:
    store = IndexStore.open(tmp_path / ".repolens" / "repolens.sqlite3")
    parser = PythonParser()
    for path, source in files.items():
        result = parser.parse(path, source)
        file_id = store.upsert_file(
            path=path, language="python", content_hash=text_hash(source), size_bytes=len(source)
        )
        store.replace_file_symbols(file_id, result.symbols)
        store.replace_file_relationships(file_id, result.relationships)
        store.replace_file_imports(file_id, result.imports)
    return store


def test_builds_file_and_symbol_nodes(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "app/utils.py": "def helper():\n    return 1\n",
            "app/service.py": "from .utils import helper\n\ndef login():\n    return helper()\n",
        },
    )
    repo_graph = build_graph(store)

    assert file_node_id("app/utils.py") in repo_graph.graph
    assert file_node_id("app/service.py") in repo_graph.graph
    assert symbol_node_id("app/utils.py", "helper") in repo_graph.graph
    assert symbol_node_id("app/service.py", "login") in repo_graph.graph


def test_resolves_cross_file_import_edge(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "app/utils.py": "def helper():\n    return 1\n",
            "app/service.py": "from .utils import helper\n\ndef login():\n    return helper()\n",
        },
    )
    repo_graph = build_graph(store)

    service_file = file_node_id("app/service.py")
    utils_file = file_node_id("app/utils.py")
    assert utils_file in dependencies_of(repo_graph, service_file)

    edge_data = repo_graph.graph.get_edge_data(service_file, utils_file)
    assert any(d.get("kind") == "imports" and d.get("resolution") == "resolved" for d in edge_data.values())


def test_resolves_unambiguous_call_edge(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "app/utils.py": "def helper():\n    return 1\n",
            "app/service.py": "from .utils import helper\n\ndef login():\n    return helper()\n",
        },
    )
    repo_graph = build_graph(store)

    login_symbol = symbol_node_id("app/service.py", "login")
    helper_symbol = symbol_node_id("app/utils.py", "helper")
    assert helper_symbol in dependencies_of(repo_graph, login_symbol)
    assert login_symbol in dependents_of(repo_graph, helper_symbol)


def test_persists_resolution_back_to_store(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "app/utils.py": "def helper():\n    return 1\n",
            "app/service.py": "from .utils import helper\n\ndef login():\n    return helper()\n",
        },
    )
    build_graph(store, persist_resolution=True)

    relationships = store.iter_all_relationships()
    assert any(r.resolution == "resolved" for r in relationships)


def test_ambiguous_call_name_stays_unresolved(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "a.py": "def run():\n    return 1\n",
            "b.py": "def run():\n    return 2\n",
            "c.py": "def main():\n    return run()\n",
        },
    )
    repo_graph = build_graph(store)
    main_symbol = symbol_node_id("c.py", "main")
    deps = dependencies_of(repo_graph, main_symbol)
    # Neither a.py::run nor b.py::run should be a resolved dependency target.
    assert symbol_node_id("a.py", "run") not in deps
    assert symbol_node_id("b.py", "run") not in deps


def test_external_import_stays_unresolved_but_recorded(tmp_path: Path) -> None:
    store = _index_python_files(tmp_path, {"app.py": "import flask\n"})
    repo_graph = build_graph(store)
    app_file = file_node_id("app.py")
    deps = dependencies_of(repo_graph, app_file)
    assert any(d.startswith("unresolved::") for d in deps)


def test_transitive_dependents(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "core.py": "def base():\n    return 1\n",
            "mid.py": "from .core import base\n\ndef mid_fn():\n    return base()\n",
            "top.py": "from .mid import mid_fn\n\ndef top_fn():\n    return mid_fn()\n",
        },
    )
    repo_graph = build_graph(store)
    base_symbol = symbol_node_id("core.py", "base")
    ancestors = transitive_dependents(repo_graph, base_symbol)
    assert symbol_node_id("mid.py", "mid_fn") in ancestors
    assert symbol_node_id("top.py", "top_fn") in ancestors


def test_important_files_ranks_most_imported_highest(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "shared.py": "X = 1\n",
            "a.py": "from .shared import X\n",
            "b.py": "from .shared import X\n",
        },
    )
    repo_graph = build_graph(store)
    ranked = important_files(repo_graph, top_n=5)
    assert ranked[0].path == "shared.py"
    assert ranked[0].fan_in == 2
