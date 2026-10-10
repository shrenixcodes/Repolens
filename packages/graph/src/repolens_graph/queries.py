"""Forward and reverse dependency queries over a built `RepoGraph`."""

from __future__ import annotations

import networkx as nx

from repolens_graph.builder import RepoGraph


def dependencies_of(repo_graph: RepoGraph, node_id: str) -> list[str]:
    """Direct outgoing edges: what ``node_id`` depends on / references."""
    if node_id not in repo_graph.graph:
        return []
    return list(repo_graph.graph.successors(node_id))


def dependents_of(repo_graph: RepoGraph, node_id: str) -> list[str]:
    """Direct incoming edges: what depends on / references ``node_id``."""
    if node_id not in repo_graph.graph:
        return []
    return list(repo_graph.graph.predecessors(node_id))


def transitive_dependents(repo_graph: RepoGraph, node_id: str, *, max_depth: int | None = None) -> set[str]:
    """Everything that depends on ``node_id``, directly or indirectly."""
    if node_id not in repo_graph.graph:
        return set()
    reversed_graph = repo_graph.graph.reverse(copy=False)
    if max_depth is None:
        return set(nx.descendants(reversed_graph, node_id))
    lengths = nx.single_source_shortest_path_length(reversed_graph, node_id, cutoff=max_depth)
    return {n for n in lengths if n != node_id}


def transitive_dependencies(repo_graph: RepoGraph, node_id: str, *, max_depth: int | None = None) -> set[str]:
    """Everything ``node_id`` depends on, directly or indirectly."""
    if node_id not in repo_graph.graph:
        return set()
    if max_depth is None:
        return set(nx.descendants(repo_graph.graph, node_id))
    lengths = nx.single_source_shortest_path_length(repo_graph.graph, node_id, cutoff=max_depth)
    return {n for n in lengths if n != node_id}


def edges_between(repo_graph: RepoGraph, source: str, target: str) -> list[dict]:
    """All relationship edges directly connecting ``source`` to ``target``."""
    if not repo_graph.graph.has_edge(source, target):
        return []
    return list(repo_graph.graph.get_edge_data(source, target).values())
