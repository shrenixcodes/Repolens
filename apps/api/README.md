# repolens-api

The RepoLens HTTP API (FastAPI). Lets the web UI (and any other client)
register repositories, trigger indexing, and run search/ask/graph/impact/
git-history queries over them.

## Running

```bash
pip install -e apps/api
uvicorn repolens_api.app:create_app --factory --host 127.0.0.1 --port 8000
```

The API binds to `127.0.0.1` by default -- it is not exposed to your
network unless you explicitly pass `--host 0.0.0.0` (or otherwise). It does
not upload repository source anywhere; a registered repository's files
never leave disk except when an LLM/embedding provider is explicitly
configured to answer a question (see `docs/security.md`).

## Repository registry

A repository must be registered (`POST /repositories`) before it can be
indexed or queried. Registration just records an absolute path on the
machine the API is running on -- it does not copy or scan anything by
itself; call `POST /repositories/{id}/index` next. The registry persists to
`~/.repolens/workspaces.json` so registered repositories survive a server
restart.

## Error handling

Every `repolens_shared.exceptions.RepoLensError` subclass maps to a
specific HTTP status with a structured `{"detail": "..."}` body:
`PathTraversalError`/`ConfigurationError` -> 400, `RepositoryNotIndexedError`
-> 409, a missing repository/symbol -> 404, `ProviderError` -> 502.
