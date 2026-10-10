# Changelog

All notable changes to this project are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Monorepo foundation: `repolens-shared` (path safety, exceptions, shared
  types), `repolens-config` (layered configuration).
- `repolens-cli` with `init`, `doctor`, `index`, `status`, `search`, `ask`,
  `impact`, and `history` commands.
- `repolens-parser`: pluggable parser registry with a stdlib-`ast` Python
  parser and a tree-sitter-based parser shared across JavaScript,
  TypeScript, and TSX, plus honest per-language coverage reporting.
- `repolens-indexer`: file discovery with layered ignore rules and a
  hard-coded secret-file exclusion list, a SQLite persistence layer with
  versioned migrations, incremental indexing, FTS5-backed lexical search,
  and chunk/embedding storage.
- `repolens-graph`: dependency/call graph construction with conservative
  cross-file resolution, forward/reverse/transitive dependency queries,
  fan-in/fan-out and PageRank-based "important files" ranking, and impact
  analysis.
- `repolens-ai`: provider-agnostic embedding and LLM abstractions with
  mock (offline, default), Ollama, and OpenAI-compatible implementations.
- `repolens-retrieval`: hybrid lexical + semantic + structural search,
  one-hop graph expansion, context-budget assembly, and grounded
  repository Q&A with source citations and prompt-injection containment.
- `repolens-git`: a safe `git` subprocess wrapper for file history, blame,
  and commit/change lookups.
- `repolens-api`: a FastAPI service exposing repository registration,
  indexing, status, search, ask, graph, file/symbol browsing, impact
  analysis, and Git history, bound to loopback by default.
- `repolens-web`: a Next.js dashboard (Dashboard, Explorer, Search, Ask,
  Graph, Impact, History screens) wired to the API.
- Docker multi-stage builds for the API and web app, with a
  loopback-bound `docker-compose.yml`.
- Project documentation, security policy, contribution guide, and CI
  workflow.

[Unreleased]: https://github.com/shrenixcodes/Repolens/commits/main
