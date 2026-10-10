from repolens_graph.resolve import SymbolNameIndex, resolve_js_import, resolve_python_import


def test_resolve_python_relative_import_sibling_module() -> None:
    known = frozenset({"src/auth/service.py", "src/auth/utils.py"})
    resolved = resolve_python_import("src/auth/service.py", ".utils", known)
    assert resolved == "src/auth/utils.py"


def test_resolve_python_relative_import_package_init() -> None:
    known = frozenset({"src/auth/service.py", "src/auth/__init__.py"})
    resolved = resolve_python_import("src/auth/service.py", ".", known)
    assert resolved == "src/auth/__init__.py"


def test_resolve_python_absolute_import_local_package() -> None:
    known = frozenset({"src/auth/service.py", "src/db/models.py"})
    resolved = resolve_python_import("src/auth/service.py", "src.db.models", known)
    assert resolved == "src/db/models.py"


def test_resolve_python_import_of_external_package_is_none() -> None:
    known = frozenset({"src/auth/service.py"})
    assert resolve_python_import("src/auth/service.py", "os", known) is None
    assert resolve_python_import("src/auth/service.py", "requests", known) is None


def test_resolve_js_relative_import_with_extension_guessing() -> None:
    known = frozenset({"src/components/Button.tsx", "src/App.tsx"})
    resolved = resolve_js_import("src/App.tsx", "./components/Button", known)
    assert resolved == "src/components/Button.tsx"


def test_resolve_js_relative_import_to_index_file() -> None:
    known = frozenset({"src/utils/index.ts", "src/App.tsx"})
    resolved = resolve_js_import("src/App.tsx", "./utils", known)
    assert resolved == "src/utils/index.ts"


def test_resolve_js_bare_import_is_external_and_unresolved() -> None:
    known = frozenset({"src/App.tsx"})
    assert resolve_js_import("src/App.tsx", "react", known) is None


def test_symbol_name_index_resolves_unambiguous_name() -> None:
    index = SymbolNameIndex()
    index.add("helper", "src/utils.py", "helper", "function")
    assert index.resolve_unambiguous("helper") == ("src/utils.py", "helper", "function")


def test_symbol_name_index_ambiguous_name_is_unresolved() -> None:
    index = SymbolNameIndex()
    index.add("Handler", "a.py", "Handler", "class")
    index.add("Handler", "b.py", "Handler", "class")
    assert index.resolve_unambiguous("Handler") is None


def test_symbol_name_index_unknown_name_is_unresolved() -> None:
    index = SymbolNameIndex()
    assert index.resolve_unambiguous("nope") is None
