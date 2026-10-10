from repolens_parser.models import RelationshipKind, SymbolKind
from repolens_parser.python_parser import PythonParser

SOURCE = '''
"""Module docstring."""
import os
from .utils import helper, other as alias

class Animal:
    """An animal."""

    def speak(self):
        return helper(self.name)


class Dog(Animal):
    @staticmethod
    def bark():
        return "woof"


def top_level(x):
    return Dog().bark()


CONFIG = {"a": 1}
'''


def _parse():
    return PythonParser().parse("animals.py", SOURCE)


def test_extracts_classes_and_inheritance() -> None:
    result = _parse()
    classes = {s.qualified_name: s for s in result.symbols if s.kind == SymbolKind.CLASS}
    assert "Animal" in classes
    assert "Dog" in classes
    assert classes["Animal"].docstring == "An animal."

    inherits = [r for r in result.relationships if r.kind == RelationshipKind.INHERITS]
    assert any(r.source_qualified_name == "Dog" and r.target_name == "Animal" for r in inherits)


def test_extracts_methods_with_parent() -> None:
    result = _parse()
    methods = {s.qualified_name: s for s in result.symbols if s.kind == SymbolKind.METHOD}
    assert "Animal.speak" in methods
    assert methods["Animal.speak"].parent_qualified_name == "Animal"
    assert "Dog.bark" in methods
    assert methods["Dog.bark"].decorators == ("staticmethod",)


def test_extracts_top_level_function_and_variable() -> None:
    result = _parse()
    kinds = {s.qualified_name: s.kind for s in result.symbols}
    assert kinds["top_level"] == SymbolKind.FUNCTION
    assert kinds["CONFIG"] == SymbolKind.VARIABLE


def test_extracts_imports() -> None:
    result = _parse()
    modules = {i.module for i in result.imports}
    assert "os" in modules
    assert ".utils" in modules
    rel_import = next(i for i in result.imports if i.module == ".utils")
    assert rel_import.is_relative is True
    assert set(rel_import.imported_names) == {"helper", "other"}


def test_extracts_calls() -> None:
    result = _parse()
    calls = {r.target_name for r in result.relationships if r.kind == RelationshipKind.CALLS}
    assert "helper" in calls
    assert "bark" in calls


def test_syntax_error_reported_without_raising() -> None:
    result = PythonParser().parse("broken.py", "def foo(:\n    pass")
    assert result.errors
    assert result.symbols == []


def test_parser_language_and_extensions() -> None:
    parser = PythonParser()
    assert parser.language == "python"
    assert ".py" in parser.extensions
