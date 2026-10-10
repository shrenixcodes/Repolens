"""Dependency graph data for visualization."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from repolens_api.deps import get_repo_graph
from repolens_api.schemas import GraphEdge, GraphNode, GraphResponse
from repolens_graph import RepoGraph

router = APIRouter(prefix="/repositories/{repository_id}", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
def get_repository_graph(
    repo_graph: RepoGraph = Depends(get_repo_graph),
    include_symbols: bool = Query(
        False, description="Include symbol nodes/edges, not just files (can be large)."
    ),
    max_nodes: int = Query(300, ge=1, le=2000),
) -> GraphResponse:
    graph = repo_graph.graph

    candidate_ids = [
        n
        for n, data in graph.nodes(data=True)
        if data.get("node_type") in (("file", "symbol") if include_symbols else ("file",))
    ]
    truncated = len(candidate_ids) > max_nodes
    kept_ids = set(candidate_ids[:max_nodes])

    nodes = []
    for node_id in kept_ids:
        data = graph.nodes[node_id]
        label = data.get("qualified_name") or data.get("path") or node_id
        nodes.append(
            GraphNode(
                id=node_id,
                node_type=data.get("node_type", "unknown"),
                label=label,
                path=data.get("path"),
                kind=data.get("kind"),
            )
        )

    edges = [
        GraphEdge(
            source=u,
            target=v,
            kind=data.get("kind", "unknown"),
            resolution=data.get("resolution", "unresolved"),
        )
        for u, v, data in graph.edges(data=True)
        if u in kept_ids and v in kept_ids and data.get("kind") != "contains"
    ]

    return GraphResponse(nodes=nodes, edges=edges, truncated=truncated)
