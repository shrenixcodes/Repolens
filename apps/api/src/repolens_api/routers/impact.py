"""Impact analysis."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from repolens_api.deps import get_repo_graph
from repolens_api.schemas import ImpactRequest, ImpactResponse
from repolens_graph import RepoGraph, analyze_impact

router = APIRouter(prefix="/repositories/{repository_id}", tags=["impact"])


@router.post("/impact", response_model=ImpactResponse)
def analyze_repository_impact(
    payload: ImpactRequest, repo_graph: RepoGraph = Depends(get_repo_graph)
) -> ImpactResponse:
    report = analyze_impact(repo_graph, payload.target)
    return ImpactResponse(
        target=report.target,
        target_found=report.target_found,
        direct_dependents=list(report.direct_dependents),
        transitive_dependents=list(report.transitive_dependents),
        related_tests=list(report.related_tests),
        limitations=list(report.limitations),
    )
