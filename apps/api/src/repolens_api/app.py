"""The RepoLens FastAPI application factory."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from repolens_api.errors import register_exception_handlers
from repolens_api.registry import DEFAULT_REGISTRY_PATH, RepositoryRegistry
from repolens_api.routers import ask, files, git, graph, impact, repositories, search
from repolens_shared.logging import configure_logging

_DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def create_app(*, registry_path: Path = DEFAULT_REGISTRY_PATH) -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="RepoLens API",
        description="Local-first AI codebase intelligence -- repository registration, "
        "indexing, search, Q&A, graph, impact analysis, and Git history.",
        version="0.1.0",
    )
    app.state.registry = RepositoryRegistry(registry_path)

    # The web UI runs on a different port (a different origin, from the
    # browser's point of view) than this API, so it needs CORS -- but only
    # for the specific local origins the web UI actually runs on, never "*".
    raw_origins = os.environ.get("REPOLENS_CORS_ORIGINS")
    origins = [o.strip() for o in raw_origins.split(",")] if raw_origins else _DEFAULT_CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

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
