"""Repository-wide graph statistics (fan-in/fan-out, important modules)."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from repolens_graph.builder import RepoGraph
from repolens_graph.ids import is_file_node


@dataclass(frozen=True, slots=True)
class FileImportance:
    path: str
    fan_in: int
    fan_out: int
    pagerank: float


def file_fan_in_out(repo_graph: RepoGraph) -> dict[str, tuple[int, int]]:
    """Resolved-import fan-in/fan-out per file (how many other files import it / it imports)."""
    import_subgraph = nx.DiGraph()
    for node in repo_graph.file_ids:
        import_subgraph.add_node(node)
    for u, v, data in repo_graph.graph.edges(data=True):
        if (
            data.get("kind") == "imports"
            and data.get("resolution") == "resolved"
            and is_file_node(u)
            and is_file_node(v)
        ):
            import_subgraph.add_edge(u, v)

    return {
        node: (import_subgraph.in_degree(node), import_subgraph.out_degree(node))
        for node in import_subgraph.nodes
    }


def important_files(repo_graph: RepoGraph, *, top_n: int = 10) -> list[FileImportance]:
    """Rank files by import centrality.

    Combines simple fan-in/fan-out counts (easy to explain: "N files import
    this one") with PageRank over the resolved import graph (captures
    indirect importance -- a file imported by an important hub file scores
    higher even with few direct importers). Both numbers are returned so
    callers can show the simple count, not just an opaque score.
    """
    fan = file_fan_in_out(repo_graph)
    if not fan:
        return []

    import_subgraph = nx.DiGraph()
    import_subgraph.add_nodes_from(fan.keys())
    for u, v, data in repo_graph.graph.edges(data=True):
        if (
            data.get("kind") == "imports"
            and data.get("resolution") == "resolved"
            and u in fan
            and v in fan
        ):
            import_subgraph.add_edge(u, v)

    try:
        pagerank = nx.pagerank(import_subgraph) if import_subgraph.number_of_edges() else {}
    except nx.PowerIterationFailedConvergence:
        pagerank = {}

    results = [
        FileImportance(
            path=node.split("::", 1)[1],
            fan_in=fan_in,
            fan_out=fan_out,
            pagerank=pagerank.get(node, 0.0),
        )
        for node, (fan_in, fan_out) in fan.items()
    ]
    results.sort(key=lambda r: (r.pagerank, r.fan_in), reverse=True)
    return results[:top_n]
