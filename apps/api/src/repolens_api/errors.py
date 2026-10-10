"""Maps `repolens_shared` exceptions to structured HTTP error responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from repolens_shared.exceptions import (
    ConfigurationError,
    GitError,
    ParserError,
    PathTraversalError,
    ProviderError,
    RepoLensError,
    RepositoryNotIndexedError,
)

_STATUS_BY_EXCEPTION: list[tuple[type[RepoLensError], int]] = [
    (PathTraversalError, 400),
    (ConfigurationError, 400),
    (RepositoryNotIndexedError, 409),
    (ProviderError, 502),
    (GitError, 502),
    (ParserError, 500),
]


def _status_for(exc: RepoLensError) -> int:
    for exc_type, status in _STATUS_BY_EXCEPTION:
        if isinstance(exc, exc_type):
            return status
    return 500


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RepoLensError)
    async def _handle_repolens_error(_request: Request, exc: RepoLensError) -> JSONResponse:
        return JSONResponse(status_code=_status_for(exc), content={"detail": str(exc)})
