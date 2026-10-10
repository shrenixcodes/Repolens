"""Impact analysis: what might break if a file or symbol changes.

Everything here is derived from statically resolved graph edges
(`repolens_graph.resolve`). It cannot see dynamic dispatch, reflection,
string-built imports, or anything else static analysis fundamentally can't
observe -- results are phrased as "potentially affected", never as a
guarantee, and `ImpactReport.limitations` states this explicitly so no
caller (CLI, API, web UI) has to rediscover the caveat on its own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from repolens_graph.builder import RepoGraph
from repolens_graph.ids import file_node_id, is_file_node, symbol_node_id
from repolens_graph.queries import dependents_of, transitive_dependents

_TEST_PATH_RE = re.compile(
    r"(^|/)(tests?)/|(^|/)test_[^/]+\.py$|_test\.py$|\.test\.[jt]sx?$|\.spec\.[jt]sx?$"
)

LIMITATIONS = (
    "Based only on statically resolved import/call/inheritance/implements edges; "
    "dynamic dispatch, reflection, string-built imports, and unresolved (ambiguous) "
    "names are not captured here.",
    "API routes and frontend components are not automatically detected in this "
    "version -- check 'Related tests' and 'Potentially affected files' manually "
    "against your routing code.",
)


def is_test_path(path: str) -> bool:
    return bool(_TEST_PATH_RE.search(path))


@dataclass(frozen=True, slots=True)
class ImpactReport:
    target: str
    target_found: bool
    direct_dependents: tuple[str, ...] = field(default_factory=tuple)
    transitive_dependents: tuple[str, ...] = field(default_factory=tuple)
    related_tests: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = LIMITATIONS


def _label(repo_graph: RepoGraph, node_id: str) -> str:
    data = repo_graph.graph.nodes[node_id]
    if is_file_node(node_id):
        return data["path"]
    return f"{data['path']}::{data['qualified_name']}"


def _resolve_target_node(path_or_symbol: str) -> str:
    if "::" in path_or_symbol:
        path, qualified_name = path_or_symbol.split("::", 1)
        return symbol_node_id(path, qualified_name)
    return file_node_id(path_or_symbol)


def analyze_impact(repo_graph: RepoGraph, target: str) -> ImpactReport:
    """``target`` is a repository-relative file path, or ``path::qualified_name``."""
    node_id = _resolve_target_node(target)
    if node_id not in repo_graph.graph:
        return ImpactReport(target=target, target_found=False)

    direct = [n for n in dependents_of(repo_graph, node_id) if not n.startswith("unresolved::")]
    transitive = [
        n for n in transitive_dependents(repo_graph, node_id) if not n.startswith("unresolved::")
    ]

    direct_labels = tuple(sorted({_label(repo_graph, n) for n in direct}))
    transitive_labels = tuple(sorted({_label(repo_graph, n) for n in transitive}))

    affected_paths = {label.split("::", 1)[0] for label in transitive_labels} | {
        label.split("::", 1)[0] for label in direct_labels
    }
    related_tests = tuple(sorted(p for p in affected_paths if is_test_path(p)))

    return ImpactReport(
        target=target,
        target_found=True,
        direct_dependents=direct_labels,
        transitive_dependents=transitive_labels,
        related_tests=related_tests,
    )
