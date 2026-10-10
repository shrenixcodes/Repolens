# Architecture

RepoLens is a modular monorepo. Each package under `packages/` does one
thing and is installable/testable independently; the apps under `apps/`
compose them into something runnable.

## Pipeline

```
File discovery (packages/indexer)
  -> Language detection + parsing (packages/parser)
  -> Symbol/relationship extraction (packages/parser)
  -> Persistence (packages/indexer/db -- SQLite)
  -> Chunking + lexical index (packages/indexer)
  -> [optional] Embeddings (packages/ai + packages/indexer)
  -> Dependency graph + cross-file resolution (packages/graph)
  -> Hybrid retrieval (packages/retrieval)
  -> [optional] LLM generation (packages/ai)
  -> Grounded answer + citations (packages/retrieval)
```

Everything up to and including hybrid retrieval works with zero network
access and zero configuration. The LLM step is the only one that's ever
optional-by-design to skip -- and when it's skipped, retrieval's results
are still returned as cited evidence, not discarded.

## Packages

| Package | Responsibility | Depends on |
|---|---|---|
| `repolens-shared` | Path safety, exceptions, shared value types, redacting logging. Zero third-party dependencies. | -- |
| `repolens-config` | Layered config: defaults -> `repolens.yaml` -> env vars. | shared |
| `repolens-parser` | Pluggable `LanguageParser` registry; stdlib-`ast` Python parser; tree-sitter JS/TS/TSX parser; coverage reporting. | shared |
| `repolens-indexer` | File discovery + ignore rules, SQLite schema/migrations, incremental indexing pipeline, FTS5 lexical search, embedding storage + brute-force cosine search. | shared, config, parser |
| `repolens-graph` | Builds a `networkx` graph from indexed symbols/relationships; conservative cross-file resolution; dependency queries; impact analysis. | shared, indexer |
| `repolens-ai` | `EmbeddingProvider`/`LLMProvider` protocols; mock/Ollama/OpenAI-compatible implementations. | shared, config |
| `repolens-retrieval` | Hybrid lexical+semantic+structural ranking; graph expansion; context-budget assembly; grounded Q&A. | shared, indexer, graph |
| `repolens-git` | Safe `git` subprocess wrapper: history, blame, commit/change lookup. | shared |
| `repolens-cli` (`apps/cli`) | The `repolens` command. | all of the above, `repolens-ai` |
| `repolens-api` (`apps/api`) | FastAPI service; repository registry; all of the above over HTTP. | all of the above |
| `repolens-web` (`apps/web`) | Next.js dashboard. Talks only to `repolens-api` over HTTP. | -- |

Dependencies flow one direction only (shared <- config/parser <- indexer <-
graph/ai <- retrieval <- cli/api). `repolens-indexer` never imports
`repolens-ai` directly -- the indexing pipeline takes a plain callable
(`EmbeddingBackend`) for embedding generation, so the CLI/API wire a
concrete provider in without creating a dependency cycle. The same pattern
is used for Q&A's `generate_fn`.

## Data model

One SQLite database per repository, at `<repo>/.repolens/repolens.sqlite3`
by default (`database.path` in `repolens.yaml`). Tables: `files`,
`symbols`, `relationships`, `imports`, `chunks`, `chunks_fts` (FTS5
virtual table), `embeddings`, `schema_version`. See
[`packages/indexer/src/repolens_indexer/db/schema.py`](../packages/indexer/src/repolens_indexer/db/schema.py)
for the authoritative definitions.

The API additionally keeps a small JSON registry
(`~/.repolens/workspaces.json`) mapping repository IDs to absolute paths on
disk -- this is bookkeeping only, not a cache of repository content.

## Cross-file resolution

Parsers only ever see one file, so every relationship they extract starts
`unresolved` (a name, not a link). `repolens_graph.resolve` upgrades
relationships to `resolved` using two conservative heuristics -- import
paths resolved against the actual set of indexed files, and symbol names
resolved only when unambiguous across the whole repository. See
[`packages/graph/README.md`](../packages/graph/README.md) for the exact
policy and its limitations.

## Why not just send files to an LLM?

Because then the "architecture" RepoLens would show you is whatever the
model guessed, with no way to tell you *which* parts of that guess were
grounded in something real. The pipeline above exists so that every
dependency edge, every citation, and every "related symbol" in an answer
traces back to something `repolens_parser` or `repolens_git` actually
observed -- and the parts that can't be established that way (why a change
was made, whether a route handler calls a given function) are stated as
unknown rather than inferred.
