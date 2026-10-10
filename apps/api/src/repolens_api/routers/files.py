"""File listing and single-file detail (content + symbols)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from repolens_api.deps import get_repository, get_store
from repolens_api.registry import RepositoryRecord
from repolens_api.schemas import FileResponse, SymbolResponse
from repolens_indexer.db import IndexStore
from repolens_shared.exceptions import PathTraversalError
from repolens_shared.paths import resolve_within_root

router = APIRouter(prefix="/repositories/{repository_id}", tags=["files"])


@router.get("/files", response_model=list[str])
def list_files(store: IndexStore = Depends(get_store)) -> list[str]:
    return [f.path for f in store.list_files()]


@router.get("/files/{file_path:path}", response_model=FileResponse)
def get_file(
    file_path: str,
    repository: RepositoryRecord = Depends(get_repository),
    store: IndexStore = Depends(get_store),
) -> FileResponse:
    file_row = store.get_file(file_path)
    if file_row is None:
        raise HTTPException(status_code=404, detail=f"Not indexed: {file_path}")

    try:
        resolved = resolve_within_root(Path(repository.path), file_path)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content: str | None = None
    if resolved.is_file():
        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = None

    symbols = store.list_symbols_for_file(file_row.id)
    return FileResponse(
        path=file_row.path,
        language=file_row.language,
        size_bytes=file_row.size_bytes,
        content=content,
        symbols=[
            SymbolResponse(
                id=s.id,
                file_path=s.file_path,
                name=s.name,
                qualified_name=s.qualified_name,
                kind=s.kind,
                start_line=s.start_line,
                end_line=s.end_line,
                docstring=s.docstring,
                parent_qualified_name=s.parent_qualified_name,
                decorators=list(s.decorators),
                is_exported=s.is_exported,
            )
            for s in symbols
        ],
    )
