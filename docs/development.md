# Development

## Setup

```bash
git clone https://github.com/shrenixcodes/Repolens.git
cd Repolens

python -m venv .venv
source .venv/Scripts/activate   # Windows (git-bash) -- .venv/bin/activate on macOS/Linux

pip install -e packages/shared -e packages/config -e packages/parser \
            -e packages/indexer -e packages/graph -e packages/retrieval \
            -e packages/ai -e packages/git -e apps/cli -e "apps/api[test]"
pip install pytest ruff mypy

cd apps/web && npm install && cd ..
```

Order matters for the `pip install -e` line: each package's local-path
dependency on an earlier one is satisfied by the one already installed, in
one resolver pass.

## Repository layout

```
packages/
  shared/      # path safety, exceptions, shared types -- zero deps
  config/      # layered configuration
  parser/      # pluggable language parsers
  indexer/     # file discovery, SQLite persistence, lexical search
  graph/       # dependency graph, cross-file resolution, impact analysis
  ai/          # LLM/embedding provider abstractions
  retrieval/   # hybrid search, context assembly, grounded Q&A
  git/         # safe git subprocess wrapper
apps/
  cli/         # the `repolens` command
  api/         # FastAPI service
  web/         # Next.js dashboard
docs/          # this directory
examples/      # small fixture repositories to try RepoLens against
```

Each package has its own `pyproject.toml`, `README.md`, and `tests/`.
`apps/web` is a standalone Node project (`package.json`).

## Running tests

```bash
pytest                                    # everything
pytest packages/graph/tests -v            # one package
pytest -k "test_hybrid_search"            # by name
```

Tests use real temporary repositories (`tmp_path`) and a real SQLite
database per test -- no mocked filesystem, no shared state between tests.
HTTP-backed providers (Ollama/OpenAI-compatible) are tested against a
mocked `httpx` transport, never a real network call.

```bash
cd apps/web && npm run lint && npm run build
```

## Linting & type checking

```bash
ruff check packages apps
mypy packages/shared/src packages/config/src packages/parser/src \
     packages/indexer/src packages/graph/src packages/retrieval/src \
     packages/ai/src packages/git/src apps/cli/src apps/api/src
```

Both run in CI (`.github/workflows/ci.yml`) against Python 3.11 and 3.12.

## Adding a package

New functionality that's genuinely its own concern gets its own package
under `packages/`, with:

- `pyproject.toml` declaring its real dependencies (including other
  `repolens-*` packages by name, not by path).
- A `README.md` stating what it does and its known limitations -- be as
  honest here as `packages/parser/README.md` and `packages/graph/README.md`
  are about what's approximate vs. exact.
- `tests/` covering real behavior, not implementation details.

Keep the dependency direction one-way (see
[`docs/architecture.md`](architecture.md)'s package table) -- if a lower-
level package seems to need something from a higher-level one, that's a
sign the abstraction boundary is in the wrong place, not a reason to add
the import.

## Database migrations

`packages/indexer/src/repolens_indexer/db/engine.py` tracks schema version
in a `schema_version` table and applies any pending migration from
`_MIGRATIONS` in order. To change the schema: add a new `_migration_N`
function, append it to `_MIGRATIONS`, and bump `CURRENT_SCHEMA_VERSION` in
`schema.py`. Never edit an already-shipped migration function -- add a new
one, even for a small follow-up fix.
