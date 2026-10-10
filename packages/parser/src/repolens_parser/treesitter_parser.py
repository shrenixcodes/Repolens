"""JavaScript/TypeScript/TSX parsing via tree-sitter.

One generic walker handles all three grammars: the JS, TS, and TSX grammars
share node type names for the constructs we extract (``class_declaration``,
``function_declaration``, ``method_definition``, ``call_expression``,
``import_statement``), with TypeScript's grammar adding a few extra node
types (``interface_declaration``, ``type_alias_declaration``,
``implements_clause``) that simply never appear when parsing plain JS.
"""

from __future__ import annotations

from tree_sitter import Language, Node, Parser

from repolens_parser.models import (
    ParsedImport,
    ParsedRelationship,
    ParsedSymbol,
    ParseResult,
    RelationshipKind,
    SymbolKind,
)
from repolens_shared.types import SourceLocation

_NAME_FIELD_NODE_TYPES = {
    "identifier",
    "type_identifier",
    "property_identifier",
    "member_expression",
    "nested_type_identifier",
    "generic_type",
}


def _text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _loc(path: str, node: Node) -> SourceLocation:
    return SourceLocation(
        path=path, start_line=node.start_point[0] + 1, end_line=node.end_point[0] + 1
    )


def _string_literal_value(source: bytes, node: Node) -> str | None:
    """Extract the raw contents of a `string` node (quotes stripped)."""
    for child in node.children:
        if child.type == "string_fragment":
            return _text(source, child)
    text = _text(source, node)
    return text[1:-1] if len(text) >= 2 else text


def _heritage_relationships(
    source: bytes, path: str, qualified: str, heritage: Node
) -> list[ParsedRelationship]:
    relationships: list[ParsedRelationship] = []
    mode: RelationshipKind | None = None

    def emit(kind: RelationshipKind, target: Node) -> None:
        relationships.append(
            ParsedRelationship(
                kind=kind,
                source_qualified_name=qualified,
                target_name=_text(source, target),
                location=_loc(path, target),
            )
        )

    for child in heritage.children:
        if child.type == "extends_clause":
            for grandchild in child.children:
                if grandchild.type in _NAME_FIELD_NODE_TYPES:
                    emit(RelationshipKind.INHERITS, grandchild)
                    break
        elif child.type == "implements_clause":
            for grandchild in child.children:
                if grandchild.type in _NAME_FIELD_NODE_TYPES:
                    emit(RelationshipKind.IMPLEMENTS, grandchild)
        elif child.type == "extends":
            mode = RelationshipKind.INHERITS
        elif child.type == "implements":
            mode = RelationshipKind.IMPLEMENTS
        elif child.type in _NAME_FIELD_NODE_TYPES and mode is not None:
            emit(mode, child)

    return relationships


class _Walker:
    def __init__(self, path: str, source: bytes) -> None:
        self.path = path
        self.source = source
        self.symbols: list[ParsedSymbol] = []
        self.relationships: list[ParsedRelationship] = []
        self.imports: list[ParsedImport] = []

    def _current_scope(self, scope_stack: list[str]) -> str:
        return ".".join(scope_stack) if scope_stack else "<module>"

    def walk(self, node: Node, scope_stack: list[str], exported: bool) -> None:
        for child in node.children:
            self._visit(child, scope_stack, exported)

    def _visit(self, node: Node, scope_stack: list[str], exported: bool) -> None:
        t = node.type

        if t == "import_statement":
            self._handle_import(node)
            return

        if t == "export_statement":
            declaration = next(
                (c for c in node.children if c.type not in ("export", "default", ";")), None
            )
            if declaration is not None:
                self._visit(declaration, scope_stack, True)
            return

        if t == "class_declaration":
            self._handle_class(node, scope_stack, exported)
            return

        if t == "interface_declaration":
            self._handle_interface(node, scope_stack, exported)
            return

        if t == "type_alias_declaration":
            self._handle_type_alias(node, scope_stack, exported)
            return

        if t == "function_declaration":
            self._handle_function(node, scope_stack, exported)
            return

        if t in ("lexical_declaration", "variable_declaration"):
            self._handle_variable_declaration(node, scope_stack, exported)
            return

        if t == "call_expression":
            self._handle_call(node, scope_stack)
            # fall through: still walk children (nested calls as arguments)

        self.walk(node, scope_stack, exported)

    def _handle_import(self, node: Node) -> None:
        source_node = node.child_by_field_name("source")
        module = _string_literal_value(self.source, source_node) if source_node else None
        if module is None:
            return
        clause = next((c for c in node.children if c.type == "import_clause"), None)
        names: list[str] = []
        if clause is not None:
            names = [
                _text(self.source, n)
                for n in clause.children
                if n.type in ("identifier", "property_identifier")
            ]
            for spec in _descendants_of_type(clause, "import_specifier"):
                binding = spec.child_by_field_name("alias") or spec.child_by_field_name("name")
                if binding is not None:
                    names.append(_text(self.source, binding))
        loc = _loc(self.path, node)
        self.imports.append(
            ParsedImport(
                module=module,
                location=loc,
                imported_names=tuple(dict.fromkeys(names)),
                is_relative=module.startswith("."),
            )
        )
        self.relationships.append(
            ParsedRelationship(
                kind=RelationshipKind.IMPORTS,
                source_qualified_name="<module>",
                target_name=module,
                location=loc,
            )
        )

    def _handle_class(self, node: Node, scope_stack: list[str], exported: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _text(self.source, name_node)
        qualified = ".".join([*scope_stack, name])
        self.symbols.append(
            ParsedSymbol(
                name=name,
                qualified_name=qualified,
                kind=SymbolKind.CLASS,
                location=_loc(self.path, node),
                parent_qualified_name=self._current_scope(scope_stack) if scope_stack else None,
                is_exported=exported,
            )
        )
        heritage = next((c for c in node.children if c.type == "class_heritage"), None)
        if heritage is not None:
            self.relationships.extend(
                _heritage_relationships(self.source, self.path, qualified, heritage)
            )
        body = node.child_by_field_name("body")
        new_scope = [*scope_stack, name]
        if body is not None:
            for member in body.children:
                if member.type == "method_definition":
                    self._handle_method(member, new_scope)
                else:
                    self.walk(member, new_scope, False)

    def _handle_method(self, node: Node, scope_stack: list[str]) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _text(self.source, name_node)
        qualified = ".".join([*scope_stack, name])
        self.symbols.append(
            ParsedSymbol(
                name=name,
                qualified_name=qualified,
                kind=SymbolKind.METHOD,
                location=_loc(self.path, node),
                parent_qualified_name=self._current_scope(scope_stack),
            )
        )
        body = node.child_by_field_name("body")
        if body is not None:
            self.walk(body, [*scope_stack, name], False)

    def _handle_interface(self, node: Node, scope_stack: list[str], exported: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _text(self.source, name_node)
        qualified = ".".join([*scope_stack, name])
        self.symbols.append(
            ParsedSymbol(
                name=name,
                qualified_name=qualified,
                kind=SymbolKind.INTERFACE,
                location=_loc(self.path, node),
                parent_qualified_name=self._current_scope(scope_stack) if scope_stack else None,
                is_exported=exported,
            )
        )
        heritage = next((c for c in node.children if c.type == "extends_type_clause"), None)
        if heritage is not None:
            for target in _descendants_of_type(heritage, "type_identifier"):
                self.relationships.append(
                    ParsedRelationship(
                        kind=RelationshipKind.INHERITS,
                        source_qualified_name=qualified,
                        target_name=_text(self.source, target),
                        location=_loc(self.path, target),
                    )
                )

    def _handle_type_alias(self, node: Node, scope_stack: list[str], exported: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _text(self.source, name_node)
        self.symbols.append(
            ParsedSymbol(
                name=name,
                qualified_name=".".join([*scope_stack, name]),
                kind=SymbolKind.TYPE_ALIAS,
                location=_loc(self.path, node),
                parent_qualified_name=self._current_scope(scope_stack) if scope_stack else None,
                is_exported=exported,
            )
        )

    def _handle_function(self, node: Node, scope_stack: list[str], exported: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _text(self.source, name_node)
        qualified = ".".join([*scope_stack, name])
        self.symbols.append(
            ParsedSymbol(
                name=name,
                qualified_name=qualified,
                kind=SymbolKind.FUNCTION,
                location=_loc(self.path, node),
                parent_qualified_name=self._current_scope(scope_stack) if scope_stack else None,
                is_exported=exported,
            )
        )
        body = node.child_by_field_name("body")
        if body is not None:
            self.walk(body, [*scope_stack, name], False)

    def _handle_variable_declaration(
        self, node: Node, scope_stack: list[str], exported: bool
    ) -> None:
        for declarator in node.children:
            if declarator.type != "variable_declarator":
                continue
            name_node = declarator.child_by_field_name("name")
            value_node = declarator.child_by_field_name("value")
            if name_node is None or name_node.type != "identifier":
                if value_node is not None:
                    self.walk(value_node, scope_stack, False)
                continue
            name = _text(self.source, name_node)

            if value_node is not None and value_node.type in ("arrow_function", "function"):
                qualified = ".".join([*scope_stack, name])
                self.symbols.append(
                    ParsedSymbol(
                        name=name,
                        qualified_name=qualified,
                        kind=SymbolKind.FUNCTION,
                        location=_loc(self.path, node),
                        parent_qualified_name=self._current_scope(scope_stack)
                        if scope_stack
                        else None,
                        is_exported=exported,
                    )
                )
                body = value_node.child_by_field_name("body")
                if body is not None:
                    self.walk(body, [*scope_stack, name], False)
            else:
                if not scope_stack:
                    self.symbols.append(
                        ParsedSymbol(
                            name=name,
                            qualified_name=name,
                            kind=SymbolKind.VARIABLE,
                            location=_loc(self.path, node),
                            is_exported=exported,
                        )
                    )
                if value_node is not None:
                    self.walk(value_node, scope_stack, False)

    def _handle_call(self, node: Node, scope_stack: list[str]) -> None:
        func = node.child_by_field_name("function")
        if func is None:
            return
        target: str | None
        if func.type == "identifier":
            target = _text(self.source, func)
        elif func.type == "member_expression":
            prop = func.child_by_field_name("property")
            target = _text(self.source, prop) if prop is not None else None
        else:
            target = None
        if target is None:
            return
        self.relationships.append(
            ParsedRelationship(
                kind=RelationshipKind.CALLS,
                source_qualified_name=self._current_scope(scope_stack),
                target_name=target,
                location=_loc(self.path, node),
            )
        )


def _descendants_of_type(node: Node, type_name: str) -> list[Node]:
    found: list[Node] = []
    for child in node.children:
        if child.type == type_name:
            found.append(child)
        found.extend(_descendants_of_type(child, type_name))
    return found


class _TreeSitterParser:
    language: str
    extensions: frozenset[str]
    _ts_language: Language

    def parse(self, path: str, source: str) -> ParseResult:
        source_bytes = source.encode("utf-8")
        parser = Parser(self._ts_language)
        tree = parser.parse(source_bytes)

        errors = []
        if tree.root_node.has_error:
            errors.append("source contains syntax errors; parse result may be incomplete")

        walker = _Walker(path, source_bytes)
        walker.walk(tree.root_node, [], False)

        return ParseResult(
            path=path,
            language=self.language,
            symbols=walker.symbols,
            relationships=walker.relationships,
            imports=walker.imports,
            errors=errors,
        )


class JavaScriptParser(_TreeSitterParser):
    language = "javascript"
    extensions = frozenset({".js", ".jsx", ".mjs", ".cjs"})

    def __init__(self) -> None:
        import tree_sitter_javascript as tsjs

        self._ts_language = Language(tsjs.language())


class TypeScriptParser(_TreeSitterParser):
    language = "typescript"
    extensions = frozenset({".ts"})

    def __init__(self) -> None:
        import tree_sitter_typescript as tsts

        self._ts_language = Language(tsts.language_typescript())


class TsxParser(_TreeSitterParser):
    language = "tsx"
    extensions = frozenset({".tsx"})

    def __init__(self) -> None:
        import tree_sitter_typescript as tsts

        self._ts_language = Language(tsts.language_tsx())
