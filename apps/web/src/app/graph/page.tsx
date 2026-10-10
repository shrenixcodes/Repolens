"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Link from "next/link";
import { api, type GraphData } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";

const COLORS: Record<string, string> = {
  file: "#5fb3b3",
  symbol: "#d9a96b",
  unresolved: "#4a5160",
};

function layoutNodes(graphNodes: GraphData["nodes"]): Node[] {
  const columns = Math.max(1, Math.ceil(Math.sqrt(graphNodes.length)));
  const spacingX = 220;
  const spacingY = 110;
  return graphNodes.map((n, i) => ({
    id: n.id,
    position: { x: (i % columns) * spacingX, y: Math.floor(i / columns) * spacingY },
    data: { label: n.label, raw: n },
    style: {
      background: "#12151a",
      color: "#d8dee6",
      border: `1px solid ${COLORS[n.node_type] ?? "#242a32"}`,
      borderRadius: 6,
      fontSize: 11,
      fontFamily: "ui-monospace, monospace",
      padding: 6,
      width: 200,
    },
  }));
}

function layoutEdges(graphEdges: GraphData["edges"]): Edge[] {
  return graphEdges.map((e, i) => ({
    id: `${e.source}->${e.target}-${i}`,
    source: e.source,
    target: e.target,
    label: e.kind,
    animated: e.resolution !== "resolved",
    style: { stroke: e.resolution === "resolved" ? "#5fb3b3" : "#4a5160", opacity: 0.6 },
    labelStyle: { fill: "#8891a0", fontSize: 9 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#5fb3b3" },
  }));
}

export default function GraphPage() {
  const { selected } = useRepo();
  const [data, setData] = useState<GraphData | null>(null);
  const [includeSymbols, setIncludeSymbols] = useState(false);
  const [filter, setFilter] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphData["nodes"][number] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (!selected) return;
    setData(null);
    setLoading(true);
    setError(null);
    api
      .getGraph(selected.id, includeSymbols)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load graph"))
      .finally(() => setLoading(false));
  }, [selected, includeSymbols]);

  const filteredNodeIds = useMemo(() => {
    if (!data || !filter.trim()) return null;
    const needle = filter.toLowerCase();
    return new Set(data.nodes.filter((n) => n.label.toLowerCase().includes(needle)).map((n) => n.id));
  }, [data, filter]);

  useEffect(() => {
    if (!data) {
      setNodes([]);
      setEdges([]);
      return;
    }
    const base = layoutNodes(data.nodes);
    const withFilter = filteredNodeIds
      ? base.map((n) => ({
          ...n,
          style: { ...n.style, opacity: filteredNodeIds.has(n.id) ? 1 : 0.15 },
        }))
      : base;
    setNodes(withFilter);
    setEdges(layoutEdges(data.edges));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, filteredNodeIds]);

  const handleNodeClick = useCallback(
    (_: unknown, node: Node) => {
      const raw = data?.nodes.find((n) => n.id === node.id) ?? null;
      setSelectedNode(raw);
    },
    [data],
  );

  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-medium">Dependency graph</h1>
        <label className="flex items-center gap-1.5 text-xs text-[var(--muted)]">
          <input
            type="checkbox"
            checked={includeSymbols}
            onChange={(e) => setIncludeSymbols(e.target.checked)}
          />
          include symbols
        </label>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter nodes..."
          className="rounded border border-[var(--border)] bg-[var(--surface)] px-2 py-1 font-mono text-xs outline-none focus:border-[var(--accent)]"
        />
        {data?.truncated && (
          <span className="text-xs text-[var(--warn)]">
            Graph truncated for display -- not all nodes shown.
          </span>
        )}
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && <p className="text-sm text-[var(--muted)]">Loading graph...</p>}

      {data && (
        <div
          className="grid grid-cols-[1fr_260px] grid-rows-[1fr] gap-3"
          style={{ height: "calc(100vh - 200px)" }}
        >
          <div
            className="h-full w-full overflow-hidden rounded border border-[var(--border)] bg-[var(--background)]"
            style={{ height: "100%", width: "100%" }}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={handleNodeClick}
              fitView
              colorMode="dark"
            >
              <Background color="#242a32" gap={24} />
              <Controls />
              <MiniMap pannable zoomable style={{ background: "#12151a" }} />
            </ReactFlow>
          </div>

          <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
            <h2 className="mb-2 text-xs font-medium text-[var(--muted)]">Selection</h2>
            {!selectedNode && <p className="text-xs text-[var(--muted)]">Click a node.</p>}
            {selectedNode && (
              <div className="flex flex-col gap-2">
                <p className="font-mono text-xs break-all">{selectedNode.label}</p>
                <p className="text-xs text-[var(--muted)]">type: {selectedNode.node_type}</p>
                {selectedNode.kind && (
                  <p className="text-xs text-[var(--muted)]">kind: {selectedNode.kind}</p>
                )}
                {selectedNode.path && (
                  <Link
                    href={`/impact?target=${encodeURIComponent(selectedNode.path)}`}
                    className="mt-1 inline-block rounded border border-[var(--border)] px-2 py-1 text-center text-xs text-[var(--accent-strong)]"
                  >
                    Analyze impact
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
