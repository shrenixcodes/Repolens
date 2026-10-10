"""One-hop graph expansion around retrieved results."""

from __future__ import annotations

from repolens_graph.builder import RepoGraph
from repolens_graph.ids import is_symbol_node, symbol_node_id
from repolens_retrieval.models import RelatedSymbolRef, RetrievedChunk

_RELATION_LABELS = {
    ("out", "calls"): "calls",
    ("in", "calls"): "called_by",
    ("out", "imports"): "imports",
    ("in", "imports"): "imported_by",
    ("out", "inherits"): "inherits",
    ("in", "inherits"): "inherited_by",
    ("out", "implements"): "implements",
    ("in", "implements"): "implemented_by",
}


def expand_with_graph(
    repo_graph: RepoGraph, chunks: list[RetrievedChunk], *, max_related_per_chunk: int = 5
) -> list[RelatedSymbolRef]:
    """Pull in symbols one hop away from each chunk's defining symbol.

    Chunks with no associated symbol (whole-file chunks for non-code files)
    contribute nothing -- there's no graph node to expand from.
    """
    graph = repo_graph.graph
    related: list[RelatedSymbolRef] = []
    seen: set[tuple[str, str]] = set()

    for chunk in chunks:
        if chunk.symbol_qualified_name is None:
            continue
        node_id = symbol_node_id(chunk.file_path, chunk.symbol_qualified_name)
        if node_id not in graph:
            continue

        count = 0
        for _, target, data in graph.out_edges(node_id, data=True):
            if count >= max_related_per_chunk:
                break
            if not is_symbol_node(target) or data.get("resolution") != "resolved":
                continue
            node_data = graph.nodes[target]
            dedup_key = (node_data["path"], node_data["qualified_name"])
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            related.append(
                RelatedSymbolRef(
                    file_path=node_data["path"],
                    qualified_name=node_data["qualified_name"],
                    relation=_RELATION_LABELS.get(("out", data.get("kind")), data.get("kind")),
                )
            )
            count += 1

        for source, _, data in graph.in_edges(node_id, data=True):
            if count >= max_related_per_chunk:
                break
            if not is_symbol_node(source) or data.get("resolution") != "resolved":
                continue
            node_data = graph.nodes[source]
            dedup_key = (node_data["path"], node_data["qualified_name"])
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            related.append(
                RelatedSymbolRef(
                    file_path=node_data["path"],
                    qualified_name=node_data["qualified_name"],
                    relation=_RELATION_LABELS.get(("in", data.get("kind")), data.get("kind")),
                )
            )
            count += 1

    return related
