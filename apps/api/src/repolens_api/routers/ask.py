"""Repository Q&A."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from repolens_ai import build_embedding_provider, build_llm_provider
from repolens_api.deps import get_repo_config, get_repo_graph, get_store
from repolens_api.schemas import AskRequest, AskResponse, CitationItem, RelatedSymbolItem
from repolens_config import RepoLensConfig
from repolens_graph import RepoGraph
from repolens_indexer.db import IndexStore
from repolens_retrieval import answer_question

router = APIRouter(prefix="/repositories/{repository_id}", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_repository(
    payload: AskRequest,
    store: IndexStore = Depends(get_store),
    repo_graph: RepoGraph = Depends(get_repo_graph),
    config: RepoLensConfig = Depends(get_repo_config),
) -> AskResponse:
    llm = build_llm_provider(config.llm)
    embedding_provider = build_embedding_provider(config.embedding) if config.indexing.enable_embeddings else None

    result = answer_question(
        store,
        repo_graph,
        payload.question,
        generate_fn=lambda prompt, system: llm.generate(prompt, system=system),
        embed_fn=embedding_provider.embed if embedding_provider else None,
        embedding_provider=embedding_provider.name if embedding_provider else None,
        embedding_model=embedding_provider.model if embedding_provider else None,
    )

    return AskResponse(
        answer=result.answer,
        grounded=result.grounded,
        citations=[
            CitationItem(
                path=c.location.path,
                start_line=c.location.start_line,
                end_line=c.location.end_line,
                symbol=c.symbol_name,
                excerpt=c.excerpt,
            )
            for c in result.citations
        ],
        related_symbols=[
            RelatedSymbolItem(path=r.file_path, qualified_name=r.qualified_name, relation=r.relation)
            for r in result.related_symbols
        ],
    )
