"""Repository registration, indexing, and status."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from repolens_api.deps import get_registry, get_repository
from repolens_api.registry import RepositoryRecord, RepositoryRegistry
from repolens_api.schemas import (
    IndexResponse,
    RepositoryCreateRequest,
    RepositoryResponse,
    StatusResponse,
)
from repolens_config import load_config
from repolens_indexer import get_status, run_index
from repolens_indexer.db import IndexStore
from repolens_indexer.pipeline import index_db_path

router = APIRouter(prefix="/repositories", tags=["repositories"])


def _to_response(record: RepositoryRecord) -> RepositoryResponse:
    return RepositoryResponse(id=record.id, path=record.path, created_at=record.created_at)


@router.post("", response_model=RepositoryResponse)
def create_repository(
    payload: RepositoryCreateRequest, registry: RepositoryRegistry = Depends(get_registry)
) -> RepositoryResponse:
    path = Path(payload.path)
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {payload.path}")
    record = registry.register(path)
    return _to_response(record)


@router.get("", response_model=list[RepositoryResponse])
def list_repositories(registry: RepositoryRegistry = Depends(get_registry)) -> list[RepositoryResponse]:
    return [_to_response(r) for r in registry.list()]


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository_endpoint(
    repository: RepositoryRecord = Depends(get_repository),
) -> RepositoryResponse:
    return _to_response(repository)


@router.post("/{repository_id}/index", response_model=IndexResponse)
def index_repository(repository: RepositoryRecord = Depends(get_repository)) -> IndexResponse:
    repo_root = Path(repository.path)
    config = load_config(repo_root)

    embedding_backend = None
    if config.indexing.enable_embeddings:
        from repolens_ai import build_embedding_provider
        from repolens_indexer import EmbeddingBackend

        provider = build_embedding_provider(config.embedding)
        embedding_backend = EmbeddingBackend(
            provider=provider.name, model=provider.model, embed_batch=provider.embed_batch
        )

    result = run_index(repo_root, config, embedding_backend=embedding_backend)
    return IndexResponse(
        files_scanned=result.files_scanned,
        files_indexed=result.files_indexed,
        files_unchanged=result.files_unchanged,
        files_removed=result.files_removed,
        files_failed=result.files_failed,
        errors=[{"path": p, "message": m} for p, m in result.errors],
    )


@router.get("/{repository_id}/status", response_model=StatusResponse)
def get_repository_status(repository: RepositoryRecord = Depends(get_repository)) -> StatusResponse:
    repo_root = Path(repository.path)
    config = load_config(repo_root)
    db_path = index_db_path(repo_root, config)
    if not db_path.exists():
        raise HTTPException(
            status_code=409, detail="This repository has not been indexed yet."
        )
    store = IndexStore.open(db_path)
    try:
        s = get_status(store)
    finally:
        store.close()
    return StatusResponse(
        total_files=s.total_files,
        total_symbols=s.total_symbols,
        total_relationships=s.total_relationships,
        resolved_relationships=s.resolved_relationships,
        files_by_language=s.files_by_language,
        symbols_by_kind=s.symbols_by_kind,
        last_indexed_at=s.last_indexed_at,
    )
