# RepoLens Development Plan

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

This checklist tracks implementation milestone by milestone. Each checked item
corresponds to at least one focused, independently tested commit. Update this
file as part of the commit that completes the item.

## Milestone 0 — Inspection & Planning
- [x] Inspect repository, git history, and working tree state
- [x] Inspect local environment (Python, Node, package managers, DBs, CLI tools)
- [x] Write and commit this plan

## Milestone 1 — Foundation
- [x] Root project layout (`apps/`, `packages/`, `docs/`, `examples/`, `tests/`, `.github/`)
- [x] `.gitignore`, `.editorconfig`
- [x] `packages/shared` — common types/exceptions/path-safety utilities
- [x] `packages/config` — layered configuration (defaults, YAML file, env vars)
- [x] Root `pyproject.toml` workspace wiring + dev dependency set (pytest, ruff, mypy)
- [x] Logging setup with secret redaction

## Milestone 2 — CLI foundation & repository discovery
- [x] `apps/cli` skeleton (`repolens --help`, `--version`)
- [x] `repolens doctor` (environment diagnostics)
- [x] `packages/indexer` file discovery + ignore rules (`.gitignore` + defaults)
- [x] Path-traversal safety tests for discovery

## Milestone 3 — Parser architecture & language support
- [x] `packages/parser` pluggable parser registry
- [x] Python parser (stdlib `ast`)
- [x] JavaScript/TypeScript/TSX parser (tree-sitter)
- [x] Parser coverage reporting (what was/wasn't understood)
- [x] Unit tests against fixture snippets

## Milestone 4 — Symbol storage & relationship extraction
- [x] SQLite schema + migrations (files, symbols, relationships, imports; chunks/commits land in M8/M13)
- [x] Symbol persistence layer (`IndexStore`)
- [x] Import/call/inheritance relationship extraction (Python + JS/TS) -- done in Milestone 3's parsers
- [x] Confidence/resolution-status field on relationships

## Milestone 5 — Graph operations
- [x] `packages/graph` build graph from stored symbols/relationships (networkx)
- [x] Forward/reverse dependency queries
- [x] Graph stats (important modules, fan-in/fan-out)

## Milestone 6 — Incremental indexing
- [x] Content hashing + change detection
- [x] `repolens index` CLI command wired to real pipeline
- [x] Re-index only changed files; delete-stale-row handling
- [x] `repolens status` reporting
- [x] `repolens init` (bonus: writes a default repolens.yaml)

## Milestone 7 — Lexical search
- [x] Chunk generation (one per top-level symbol, or whole-file for non-code files)
- [x] SQLite FTS5 full-text index over chunk content, with a query-sanitizing layer
- [x] `repolens search` command

## Milestone 8 — Embeddings & semantic search (optional layer)
- [x] `packages/ai` embedding provider interface
- [x] Mock provider (deterministic, offline, default for tests)
- [x] Ollama embedding provider
- [x] OpenAI-compatible embedding provider
- [x] Vector storage (SQLite blob + brute-force cosine; documented upgrade path)
- [x] Pipeline wiring: `indexing.enable_embeddings` + `repolens index` computes/stores embeddings

## Milestone 9 — Hybrid retrieval
- [x] `packages/retrieval` combine lexical + semantic + structural signals
- [x] Graph expansion around candidate symbols (`expand_with_graph`, one hop)
- [x] Context budget management + dedup (`assemble_context`, merge-by-location dedup in `hybrid_search`)

## Milestone 10 — AI provider interfaces & repository Q&A
- [x] LLM provider interface, mock/Ollama/OpenAI-compatible implementations
- [x] Provider selection via config/env, local-first default (mock when unset)
- [x] `repolens ask` wired to retrieval + generation

## Milestone 11 — Source-grounded citations
- [x] Citation objects attached to every answer (`answer_question` -> `AnswerResult.citations`, derived only from real retrieval results, never parsed from LLM free text)
- [x] "insufficient evidence" fallback path (no fabrication) -- `NO_EVIDENCE_MESSAGE` when retrieval finds nothing
- [x] Repository content fenced as data in the LLM prompt (prompt-injection containment)

## Milestone 12 — Impact analysis
- [x] Direct/transitive dependents via graph traversal
- [x] Related-test detection heuristic (path-convention based: test_*.py, *_test.py, *.test.ts(x), *.spec.ts(x), tests/ dirs)
- [x] `repolens impact` command
- [x] Known limitation: route/frontend-component detection not implemented; absolute-import resolution assumes import path mirrors repo-relative layout (misses src/-layout offsets)

## Milestone 13 — Git intelligence
- [ ] `packages/git` wrapper around local git (subprocess, no shell=True)
- [ ] File history, blame, commit lookup
- [ ] `repolens history` command
- [ ] Change-reason answering limited to actual commit evidence

## Milestone 14 — API completion
- [ ] `apps/api` FastAPI app, Pydantic models, error handling
- [ ] Repository/index/search/ask/graph/symbol/impact/git endpoints
- [ ] Input validation + path-traversal guards at API boundary
- [ ] Bind to 127.0.0.1 by default

## Milestone 15 — Web dashboard & explorer
- [ ] `apps/web` Next.js + TS + Tailwind scaffold
- [ ] Dashboard screen (index status, stats) wired to API
- [ ] Explorer screen (file/symbol tree) wired to API

## Milestone 16 — Search & Q&A interfaces
- [ ] Search screen wired to API
- [ ] Ask/chat screen wired to API with citations displayed

## Milestone 17 — Interactive graph
- [ ] React Flow dependency graph screen with filtering/zoom/search

## Milestone 18 — Docker & local deployment
- [ ] Dockerfiles (api, web) + docker-compose.yml
- [ ] Loopback-only defaults documented

## Milestone 19 — Security hardening
- [ ] Path traversal tests at every boundary (discovery, API, git)
- [ ] Secret-file exclusion defaults
- [ ] Prompt-injection containment (repo content fenced as data, never instructions)

## Milestone 20 — CI, documentation, release prep
- [ ] GitHub Actions (lint, type-check, test, build)
- [ ] README, docs/*, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG, LICENSE
- [ ] Example fixture repositories (python-project, typescript-project, fullstack-project)
- [ ] Final end-to-end manual verification pass

## Notes / known limitations (kept up to date)
- (filled in as work proceeds)
