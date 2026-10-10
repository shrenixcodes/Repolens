"""Python symbol and relationship extraction using the standard library `ast` module."""

from __future__ import annotations

import ast

from repolens_parser.models import (
    ParsedImport,
    ParsedRelationship,
    ParsedSymbol,
    ParseResult,
    RelationshipKind,
    SymbolKind,
)
from repolens_shared.types import SourceLocation


def _decorator_names(decorator_list: list[ast.expr]) -> tuple[str, ...]:
    names = []
    for dec in decorator_list:
        try:
            names.append(ast.unparse(dec))
        except Exception:
            names.append("<decorator>")
    return tuple(names)


def _base_name(base: ast.expr) -> str | None:
    try:
        return ast.unparse(base)
    except Exception:
        return None


def _location(path: str, node: ast.AST) -> SourceLocation:
    start = getattr(node, "lineno", 1)
    end = getattr(node, "end_lineno", start) or start
    return SourceLocation(path=path, start_line=start, end_line=end)


class _Visitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.symbols: list[ParsedSymbol] = []
        self.relationships: list[ParsedRelationship] = []
        self.imports: list[ParsedImport] = []
        self._scope_stack: list[str] = []

    def _qualified(self, name: str) -> str:
        return ".".join([*self._scope_stack, name])

    def _current_scope_name(self) -> str:
        return ".".join(self._scope_stack) if self._scope_stack else "<module>"

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802 -- ast visitor naming convention
        loc = _location(self.path, node)
        for alias in node.names:
            self.imports.append(
                ParsedImport(module=alias.name, location=loc, imported_names=(), is_relative=False)
            )
            self.relationships.append(
                ParsedRelationship(
                    kind=RelationshipKind.IMPORTS,
                    source_qualified_name=self._current_scope_name(),
                    target_name=alias.name,
                    location=loc,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        loc = _location(self.path, node)
        module = ("." * node.level) + (node.module or "")
        imported_names = tuple(alias.name for alias in node.names)
        self.imports.append(
            ParsedImport(
                module=module,
                location=loc,
                imported_names=imported_names,
                is_relative=node.level > 0,
            )
        )
        self.relationships.append(
            ParsedRelationship(
                kind=RelationshipKind.IMPORTS,
                source_qualified_name=self._current_scope_name(),
                target_name=module,
                location=loc,
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        qualified = self._qualified(node.name)
        self.symbols.append(
            ParsedSymbol(
                name=node.name,
                qualified_name=qualified,
                kind=SymbolKind.CLASS,
                location=_location(self.path, node),
                docstring=ast.get_docstring(node),
                parent_qualified_name=self._current_scope_name() if self._scope_stack else None,
                decorators=_decorator_names(node.decorator_list),
                is_exported=not node.name.startswith("_"),
            )
        )
        for base in node.bases:
            base_name = _base_name(base)
            if base_name is None:
                continue
            self.relationships.append(
                ParsedRelationship(
                    kind=RelationshipKind.INHERITS,
                    source_qualified_name=qualified,
                    target_name=base_name,
                    location=_location(self.path, node),
                )
            )
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = self._qualified(node.name)
        in_class = bool(self._scope_stack)
        kind = SymbolKind.METHOD if in_class else SymbolKind.FUNCTION
        self.symbols.append(
            ParsedSymbol(
                name=node.name,
                qualified_name=qualified,
                kind=kind,
                location=_location(self.path, node),
                docstring=ast.get_docstring(node),
                parent_qualified_name=self._current_scope_name() if self._scope_stack else None,
                decorators=_decorator_names(node.decorator_list),
                is_exported=not node.name.startswith("_"),
            )
        )
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        target_name: str | None = None
        func = node.func
        if isinstance(func, ast.Name):
            target_name = func.id
        elif isinstance(func, ast.Attribute):
            target_name = func.attr
        if target_name is not None:
            self.relationships.append(
                ParsedRelationship(
                    kind=RelationshipKind.CALLS,
                    source_qualified_name=self._current_scope_name(),
                    target_name=target_name,
                    location=_location(self.path, node),
                )
            )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        if not self._scope_stack:  # only record module-level (or class-body) variables
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.symbols.append(
                        ParsedSymbol(
                            name=target.id,
                            qualified_name=self._qualified(target.id),
                            kind=SymbolKind.VARIABLE,
                            location=_location(self.path, node),
                            is_exported=not target.id.startswith("_"),
                        )
                    )
        self.generic_visit(node)


class PythonParser:
    language = "python"
    extensions = frozenset({".py"})

    def parse(self, path: str, source: str) -> ParseResult:
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            return ParseResult(
                path=path,
                language=self.language,
                errors=[f"SyntaxError: {exc.msg} (line {exc.lineno})"],
            )

        visitor = _Visitor(path)
        try:
            visitor.visit(tree)
        except RecursionError:
            return ParseResult(
                path=path,
                language=self.language,
                errors=["source too deeply nested to parse (RecursionError)"],
            )

        return ParseResult(
            path=path,
            language=self.language,
            symbols=visitor.symbols,
            relationships=visitor.relationships,
            imports=visitor.imports,
        )
