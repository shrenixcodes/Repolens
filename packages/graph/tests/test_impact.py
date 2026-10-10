from pathlib import Path

from repolens_graph.builder import build_graph
from repolens_graph.impact import analyze_impact, is_test_path
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


def test_is_test_path_recognizes_common_conventions() -> None:
    assert is_test_path("tests/test_auth.py")
    assert is_test_path("test_auth.py")
    assert is_test_path("src/auth_test.py")  # Google-style suffix convention
    assert is_test_path("src/components/Button.test.tsx")
    assert is_test_path("src/components/Button.spec.ts")
    assert is_test_path("src/auth/service.py") is False


def test_unknown_target_reports_not_found(tmp_path: Path) -> None:
    store = _index_python_files(tmp_path, {"a.py": "def f():\n    return 1\n"})
    repo_graph = build_graph(store)
    report = analyze_impact(repo_graph, "does_not_exist.py")
    assert report.target_found is False
    assert report.direct_dependents == ()


def test_direct_and_transitive_dependents(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "core.py": "def base():\n    return 1\n",
            "mid.py": "from .core import base\n\ndef mid_fn():\n    return base()\n",
            "top.py": "from .mid import mid_fn\n\ndef top_fn():\n    return mid_fn()\n",
        },
    )
    repo_graph = build_graph(store)
    report = analyze_impact(repo_graph, "core.py::base")

    assert report.target_found is True
    assert "mid.py::mid_fn" in report.direct_dependents
    assert "top.py::top_fn" in report.transitive_dependents


def test_related_tests_detected(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "app/service.py": "def process():\n    return 1\n",
            "tests/test_service.py": (
                "from app.service import process\n\ndef test_process():\n    assert process() == 1\n"
            ),
        },
    )
    repo_graph = build_graph(store)
    report = analyze_impact(repo_graph, "app/service.py")

    assert "tests/test_service.py" in report.related_tests


def test_file_level_impact(tmp_path: Path) -> None:
    store = _index_python_files(
        tmp_path,
        {
            "utils.py": "def helper():\n    return 1\n",
            "service.py": "from .utils import helper\n",
        },
    )
    repo_graph = build_graph(store)
    report = analyze_impact(repo_graph, "utils.py")
    assert "service.py" in report.direct_dependents


def test_limitations_are_always_present(tmp_path: Path) -> None:
    store = _index_python_files(tmp_path, {"a.py": "def f():\n    return 1\n"})
    repo_graph = build_graph(store)
    report = analyze_impact(repo_graph, "a.py")
    assert len(report.limitations) >= 1
