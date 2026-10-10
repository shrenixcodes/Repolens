"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, HTTPException, Request

from repolens_api.registry import RepositoryRecord, RepositoryRegistry
from repolens_config import RepoLensConfig, load_config
from repolens_graph import RepoGraph, build_graph
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import index_db_path


def get_registry(request: Request) -> RepositoryRegistry:
    return request.app.state.registry  # type: ignore[no-any-return]


def get_repository(repository_id: str, registry: RepositoryRegistry = Depends(get_registry)) -> RepositoryRecord:
    record = registry.get(repository_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown repository id: {repository_id}")
    return record


def get_repo_config(repository: RepositoryRecord = Depends(get_repository)) -> RepoLensConfig:
    return load_config(Path(repository.path))


def get_store(
    repository: RepositoryRecord = Depends(get_repository),
    config: RepoLensConfig = Depends(get_repo_config),
) -> IndexStore:
    repo_root = Path(repository.path)
    db_path = index_db_path(repo_root, config)
    if not db_path.exists():
        raise HTTPException(
            status_code=409,
            detail="This repository has not been indexed yet. Call POST /repositories/{id}/index first.",
        )
    store = IndexStore.open(db_path)
    try:
        yield store
    finally:
        store.close()


def get_repo_graph(store: IndexStore = Depends(get_store)) -> RepoGraph:
    return build_graph(store)
