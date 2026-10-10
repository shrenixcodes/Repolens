# Configuration

RepoLens layers configuration: built-in defaults -> an optional
`repolens.yaml` in the repository root -> environment variables (highest
priority). `repolens init` writes a `repolens.yaml` with the current
(fully offline) defaults spelled out.

## Full reference

```yaml
llm:
  provider: mock              # mock | ollama | openai | openai_compatible
  model: llama3.1
  base_url: null              # required for openai_compatible; defaults per provider otherwise
  api_key: null                # prefer REPOLENS_LLM_API_KEY instead of committing this
  temperature: 0.1
  request_timeout_seconds: 60.0

embedding:
  provider: mock              # mock | ollama | openai | openai_compatible
  model: nomic-embed-text
  base_url: null
  api_key: null
  dimensions: 256
  request_timeout_seconds: 60.0

indexing:
  ignore: []                   # extra glob patterns, added to the built-in list (see below)
  respect_gitignore: true
  max_file_size_bytes: 1000000
  enable_embeddings: false     # semantic search is opt-in -- costs time/compute to generate

database:
  path: .repolens/repolens.sqlite3   # relative to the repository root; cannot resolve outside it

server:
  host: 127.0.0.1
  port: 8000
```

## Environment variables

Every field above has a matching environment variable, which always wins
over `repolens.yaml`:

| Variable | Maps to |
|---|---|
| `REPOLENS_LLM_PROVIDER` | `llm.provider` |
| `REPOLENS_LLM_MODEL` | `llm.model` |
| `REPOLENS_LLM_BASE_URL` | `llm.base_url` |
| `REPOLENS_LLM_API_KEY` | `llm.api_key` |
| `REPOLENS_EMBEDDING_PROVIDER` | `embedding.provider` |
| `REPOLENS_EMBEDDING_MODEL` | `embedding.model` |
| `REPOLENS_EMBEDDING_BASE_URL` | `embedding.base_url` |
| `REPOLENS_EMBEDDING_API_KEY` | `embedding.api_key` |
| `REPOLENS_DATABASE_PATH` | `database.path` |
| `REPOLENS_SERVER_HOST` | `server.host` |
| `REPOLENS_SERVER_PORT` | `server.port` |

**Always prefer environment variables for API keys.** Never commit a
`repolens.yaml` containing a real key -- `*.local.yaml` is already
git-ignored if you want a local file instead.

## Default ignore patterns

Indexing always skips (in addition to anything in your `.gitignore`, if
`respect_gitignore` is true):

```
.git, node_modules, __pycache__, .venv, venv, env, dist, build, coverage,
.next, target, vendor, .repolens, *.min.js, *.map, *.lock, *.pyc, *.pyo,
.env, .env.*, *.pem, *.key, *.sqlite3
```

`indexing.ignore` *adds* to this list; it cannot remove the hard-coded
secret-file patterns (`.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`,
`id_rsa*`, `id_ed25519*`, `*.sqlite3*`) -- see
[`docs/security.md`](security.md).

## Multiple repositories

`repolens.yaml` is per-repository: RepoLens looks for it directly in the
directory you run `repolens` in (or `--repo <path>`) -- it does not walk
upward looking for one the way `.git` discovery does, so run commands from
the repository root. The HTTP API's repository registry
(`~/.repolens/workspaces.json`) is a separate, simple list of paths -- each
registered repository still reads its own `repolens.yaml` independently.
