"""Builds a repository-wide `networkx` graph from an `IndexStore`."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from repolens_graph.ids import file_node_id, symbol_node_id
from repolens_graph.resolve import SymbolNameIndex, resolve_js_import, resolve_python_import
from repolens_indexer.db import IndexStore

_INHERITABLE_KINDS = {"class", "interface"}
_CALLABLE_KINDS = {"function", "method"}


@dataclass(frozen=True, slots=True)
class RepoGraph:
    """A built graph plus the node-id lookups needed to query it."""

    graph: nx.MultiDiGraph
    file_ids: frozenset[str]
    symbol_ids: frozenset[str]


def _language_family(path: str) -> str:
    if path.endswith(".py"):
        return "python"
    return "js"


def build_graph(store: IndexStore, *, persist_resolution: bool = True) -> RepoGraph:
    """Build the graph for the repository ``store`` indexes.

    When ``persist_resolution`` is true (the default), newly-resolved
    relationships are written back to ``store`` so later reads (and the
    next ``build_graph`` call) see them as already resolved -- resolution
    only needs to happen once per relationship, not on every graph build.
    """
    graph: nx.MultiDiGraph = nx.MultiDiGraph()

    files = store.list_files()
    known_paths = frozenset(f.path for f in files)
    file_node_ids = set()
    for f in files:
        node_id = file_node_id(f.path)
        file_node_ids.add(node_id)
        graph.add_node(node_id, node_type="file", path=f.path, language=f.language)

    symbols = store.iter_all_symbols()
    name_index = SymbolNameIndex()
    symbol_node_ids = set()
    for s in symbols:
        node_id = symbol_node_id(s.file_path, s.qualified_name)
        symbol_node_ids.add(node_id)
        graph.add_node(
            node_id,
            node_type="symbol",
            path=s.file_path,
            name=s.name,
            qualified_name=s.qualified_name,
            kind=s.kind,
            is_exported=s.is_exported,
        )
        parent_file = file_node_id(s.file_path)
        if parent_file in graph:
            graph.add_edge(parent_file, node_id, kind="contains", resolution="resolved")
        name_index.add(s.name, s.file_path, s.qualified_name, s.kind)

    relationships = store.iter_all_relationships()
    for rel in relationships:
        source_node = (
            file_node_id(rel.file_path)
            if rel.source_qualified_name == "<module>"
            else symbol_node_id(rel.file_path, rel.source_qualified_name)
        )
        if source_node not in graph:
            source_node = file_node_id(rel.file_path)

        target_node: str | None = None

        if rel.kind == "imports":
            resolver = (
                resolve_python_import
                if _language_family(rel.file_path) == "python"
                else resolve_js_import
            )
            target_path = resolver(rel.file_path, rel.target_name, known_paths)
            if target_path is not None:
                target_node = file_node_id(target_path)
        else:
            expected_kinds = (
                _INHERITABLE_KINDS if rel.kind in ("inherits", "implements") else _CALLABLE_KINDS
            )
            match = name_index.resolve_unambiguous(rel.target_name)
            if match is not None and match[2] in expected_kinds:
                target_path, target_qualified, _ = match
                target_node = symbol_node_id(target_path, target_qualified)

        resolution = "unresolved"
        if target_node is not None and target_node in graph:
            resolution = "resolved"
            if rel.resolution != "resolved":
                target_file_id, target_symbol_id = _resolve_db_ids(store, target_node)
                if persist_resolution and target_file_id is not None:
                    store.update_relationship_resolution(
                        rel.id, target_file_id=target_file_id, target_symbol_id=target_symbol_id
                    )
        else:
            # Keep the edge even when unresolved: it still records that
            # *this* file/symbol referenced *this* name, which is useful
            # evidence for retrieval even without a confirmed target.
            target_node = f"unresolved::{rel.target_name}"
            if target_node not in graph:
                graph.add_node(target_node, node_type="unresolved", name=rel.target_name)

        graph.add_edge(
            source_node,
            target_node,
            kind=rel.kind,
            resolution=resolution,
            start_line=rel.start_line,
            end_line=rel.end_line,
            raw_target=rel.target_name,
        )

    return RepoGraph(
        graph=graph, file_ids=frozenset(file_node_ids), symbol_ids=frozenset(symbol_node_ids)
    )


def _resolve_db_ids(store: IndexStore, target_node: str) -> tuple[int | None, int | None]:
    from repolens_graph.ids import is_file_node

    if is_file_node(target_node):
        path = target_node.split("::", 1)[1]
        file_row = store.get_file(path)
        return (file_row.id if file_row else None, None)

    _, rest = target_node.split("::", 1)
    path, _qualified = rest.split("::", 1)
    file_row = store.get_file(path)
    if file_row is None:
        return (None, None)
    for symbol_row in store.list_symbols_for_file(file_row.id):
        if symbol_node_id(path, symbol_row.qualified_name) == target_node:
            return (file_row.id, symbol_row.id)
    return (file_row.id, None)
