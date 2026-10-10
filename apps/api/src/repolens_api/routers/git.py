"""Git history."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from repolens_api.deps import get_repository
from repolens_api.registry import RepositoryRecord
from repolens_api.schemas import CommitItem, GitHistoryResponse
from repolens_git import file_history
from repolens_git.runner import is_git_repository

router = APIRouter(prefix="/repositories/{repository_id}", tags=["git"])


@router.get("/git/history", response_model=GitHistoryResponse)
def get_git_history(
    path: str = Query(..., description="Repository-relative file path."),
    limit: int = Query(20, ge=1, le=200),
    repository: RepositoryRecord = Depends(get_repository),
) -> GitHistoryResponse:
    repo_root = Path(repository.path)
    if not is_git_repository(repo_root):
        raise HTTPException(status_code=400, detail=f"{repo_root} is not a Git repository")

    commits = file_history(repo_root, path, limit=limit)
    return GitHistoryResponse(
        path=path,
        commits=[
            CommitItem(
                sha=c.sha,
                author_name=c.author_name,
                author_email=c.author_email,
                date=c.date,
                subject=c.subject,
            )
            for c in commits
        ],
    )
