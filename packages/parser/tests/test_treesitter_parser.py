import pytest

tree_sitter = pytest.importorskip("tree_sitter")

from repolens_parser.models import RelationshipKind, SymbolKind  # noqa: E402
from repolens_parser.treesitter_parser import (  # noqa: E402
    JavaScriptParser,
    TsxParser,
    TypeScriptParser,
)

JS_SOURCE = """
import { helper, other as alias } from './utils';
import defaultExport from 'module-name';

export class Animal {
  speak() { return helper(this.name); }
}

class Dog extends Animal {
  bark() { return "woof"; }
}

function topLevel(x) { return new Dog().bark(); }
const arrowFn = (x) => x * 2;
"""

TS_SOURCE = """
interface Shape { area(): number; }
interface Square extends Shape { side: number; }
type Point = { x: number; y: number };

class Circle implements Shape {
  area(): number { return 1; }
}
"""


def test_js_extracts_classes_functions_and_inheritance() -> None:
    result = JavaScriptParser().parse("animals.js", JS_SOURCE)
    classes = {s.qualified_name for s in result.symbols if s.kind == SymbolKind.CLASS}
    assert {"Animal", "Dog"} <= classes

    inherits = [r for r in result.relationships if r.kind == RelationshipKind.INHERITS]
    assert any(r.source_qualified_name == "Dog" and r.target_name == "Animal" for r in inherits)

    functions = {s.qualified_name for s in result.symbols if s.kind == SymbolKind.FUNCTION}
    assert "topLevel" in functions
    assert "arrowFn" in functions


def test_js_extracts_methods_and_calls() -> None:
    result = JavaScriptParser().parse("animals.js", JS_SOURCE)
    methods = {s.qualified_name for s in result.symbols if s.kind == SymbolKind.METHOD}
    assert "Animal.speak" in methods
    assert "Dog.bark" in methods

    calls = {r.target_name for r in result.relationships if r.kind == RelationshipKind.CALLS}
    assert "helper" in calls
    assert "bark" in calls


def test_js_extracts_imports() -> None:
    result = JavaScriptParser().parse("animals.js", JS_SOURCE)
    modules = {i.module for i in result.imports}
    assert "./utils" in modules
    assert "module-name" in modules
    rel_import = next(i for i in result.imports if i.module == "./utils")
    assert rel_import.is_relative is True
    assert set(rel_import.imported_names) >= {"helper", "alias"}


def test_js_marks_export_default_class_as_exported() -> None:
    result = JavaScriptParser().parse("animals.js", JS_SOURCE)
    animal = next(s for s in result.symbols if s.qualified_name == "Animal")
    assert animal.is_exported is True
    dog = next(s for s in result.symbols if s.qualified_name == "Dog")
    assert dog.is_exported is False


def test_ts_extracts_interfaces_type_aliases_and_implements() -> None:
    result = TypeScriptParser().parse("shapes.ts", TS_SOURCE)
    interfaces = {s.qualified_name for s in result.symbols if s.kind == SymbolKind.INTERFACE}
    assert {"Shape", "Square"} <= interfaces

    type_aliases = {s.qualified_name for s in result.symbols if s.kind == SymbolKind.TYPE_ALIAS}
    assert "Point" in type_aliases

    implements = [r for r in result.relationships if r.kind == RelationshipKind.IMPLEMENTS]
    assert any(r.source_qualified_name == "Circle" and r.target_name == "Shape" for r in implements)

    interface_inherits = [
        r
        for r in result.relationships
        if r.kind == RelationshipKind.INHERITS and r.source_qualified_name == "Square"
    ]
    assert any(r.target_name == "Shape" for r in interface_inherits)


def test_tsx_parses_jsx_without_crashing() -> None:
    result = TsxParser().parse("widget.tsx", "const Widget = () => <div>hello</div>;\n")
    assert not result.errors
    functions = {s.qualified_name for s in result.symbols if s.kind == SymbolKind.FUNCTION}
    assert "Widget" in functions


def test_syntax_error_reported_without_raising() -> None:
    result = JavaScriptParser().parse("broken.js", "function foo( {")
    assert result.errors
