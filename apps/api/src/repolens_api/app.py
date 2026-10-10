"""The RepoLens FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from repolens_api.errors import register_exception_handlers
from repolens_api.registry import DEFAULT_REGISTRY_PATH, RepositoryRegistry
from repolens_api.routers import ask, files, git, graph, impact, repositories, search
from repolens_shared.logging import configure_logging


def create_app(*, registry_path: Path = DEFAULT_REGISTRY_PATH) -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="RepoLens API",
        description="Local-first AI codebase intelligence -- repository registration, "
        "indexing, search, Q&A, graph, impact analysis, and Git history.",
        version="0.1.0",
    )
    app.state.registry = RepositoryRegistry(registry_path)

    register_exception_handlers(app)

    app.include_router(repositories.router)
    app.include_router(search.router)
    app.include_router(ask.router)
    app.include_router(impact.router)
    app.include_router(graph.router)
    app.include_router(files.router)
    app.include_router(git.router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
