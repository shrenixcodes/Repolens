"""Lexical search."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from repolens_api.deps import get_store
from repolens_api.schemas import SearchRequest, SearchResultItem
from repolens_indexer.db import IndexStore
from repolens_indexer.search import search_lexical

router = APIRouter(prefix="/repositories/{repository_id}", tags=["search"])


@router.post("/search", response_model=list[SearchResultItem])
def search_repository(
    payload: SearchRequest, store: IndexStore = Depends(get_store)
) -> list[SearchResultItem]:
    results = search_lexical(store, payload.query, limit=payload.limit)
    return [
        SearchResultItem(
            file_path=r.file_path,
            symbol=r.symbol_qualified_name,
            start_line=r.start_line,
            end_line=r.end_line,
            snippet=r.snippet,
            score=r.score,
        )
        for r in results
    ]
