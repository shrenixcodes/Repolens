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
- [x] `packages/git` wrapper around local git (subprocess, no shell=True)
- [x] File history, blame, commit lookup
- [x] `repolens history` command
- [x] Change-reason answering limited to actual commit evidence (surfaces real commit subjects only; never infers intent beyond the message text)

## Milestone 14 — API completion
- [x] `apps/api` FastAPI app, Pydantic models, error handling
- [x] Repository/index/status/search/ask/graph/files/symbols/impact/git endpoints
- [x] Input validation + path-traversal guards at API boundary
- [x] Bind to 127.0.0.1 by default (`repolens-api` script / `python -m repolens_api`)

## Milestone 15 — Web dashboard & explorer
- [x] `apps/web` Next.js + TS + Tailwind scaffold
- [x] Dashboard screen (index status, stats) wired to API
- [x] Explorer screen (file/symbol tree) wired to API

## Milestone 16 — Search & Q&A interfaces
- [x] Search screen wired to API
- [x] Ask/chat screen wired to API with citations displayed

## Milestone 17 — Interactive graph
- [x] React Flow dependency graph screen with filtering/zoom/search, click-through to Impact
- [x] Fixed a real CORS bug found during manual testing (API had no CORS policy)
- [~] Edge *visual* compositing not confirmed in this sandbox (no display compositor available); data flow and edge count verified correct via DOM/props inspection -- recommend a real-browser smoke test

## Milestone 18 — Docker & local deployment
- [x] Dockerfiles (api, web) + docker-compose.yml
- [x] Loopback-only defaults documented (docs/security.md, docker-compose.yml comments)
- [~] `docker build`/`docker compose up` NOT executed in this environment -- Docker Desktop's backend would not finish starting (likely no nested virtualization available here). Verified instead via: (1) `docker compose config` successfully validates the compose YAML, (2) the exact pip install sequence the API Dockerfile uses was run for real in a throwaway venv and succeeded, (3) `next build` with `output: "standalone"` was run for real and produces the file layout the web Dockerfile copies. Recommend a real `docker compose up --build` smoke test before release.

## Milestone 19 — Security hardening
- [x] Path traversal tests at every boundary (discovery, API files endpoint, git history/blame, index db path) -- all enforced via `resolve_within_root`
- [x] Secret-file exclusion defaults (hard-coded, cannot be overridden from config)
- [x] Prompt-injection containment (repo content fenced as data, never instructions; citations always derived from real retrieval, never parsed from LLM free text)
- [x] Full-repo review pass: no `shell=True`, no `eval`/`exec`, no unsafe `yaml.load`, no `pickle`, no archive extraction, no `dangerouslySetInnerHTML`
- [x] Found and fixed a real gap during review: `git show` revision argument injection (see git log) -- not reachable via any wired endpoint today, closed defensively anyway
- [x] CORS added to the API with an explicit origin allowlist (found missing during Milestone 15-17 manual browser testing)

## Milestone 20 — CI, documentation, release prep
- [x] GitHub Actions (lint, type-check, test, build) -- `.github/workflows/ci.yml`; exact command sequences validated locally before committing
- [x] README, docs/*, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG, LICENSE
- [x] Example fixture repositories (python-project, typescript-project, fullstack-project) -- each indexed, searched, asked, and impact-analyzed for real while writing their READMEs
- [x] Final end-to-end manual verification pass -- see below

### Final verification pass (what was actually run, not just claimed)
- `pytest` across all 9 Python packages: 213 passed, 2 skipped (symlinks unsupported in this sandbox), 0 failed.
- `ruff check packages apps`: clean. `mypy` across all 10 Python source trees: clean.
- `npm run lint` / `npm run build` for `apps/web`: clean.
- Live end-to-end smoke tests actually executed (not just unit-tested) against this repository and the three example repos: `repolens init/index/status/search/ask/impact/history` via the real installed CLI; the FastAPI app run with `python -m repolens_api` and exercised via real HTTP requests (register/index/search/ask/impact/graph/files/git history); the Next.js dashboard run with `npm run dev` and driven through a real browser for every screen.
- Found and fixed two real bugs this way that unit tests alone hadn't caught: a missing CORS policy on the API (blocked every browser fetch from the web app) and a CSS layout bug that suppressed the "parent needs a size" warning path in the Graph page.
- `docker build`/`docker compose up` were **not** executed -- see Milestone 18's note. Treat Docker as reviewed-but-unverified until someone runs it for real.
- The web Graph screen's edges were verified structurally correct (API response shape, props passed to React Flow) but not visually confirmed compositing, because this sandbox's browser pane has no display compositor -- see Milestone 17's note.

## Notes / known limitations (kept up to date)
- Cross-file relationship resolution (`repolens_graph.resolve`) is a
  conservative, name-based heuristic: absolute Python imports are resolved
  assuming the import path mirrors the repo-relative directory layout,
  which misses `src/`-layout packages installed in editable mode (their
  import path and repo-relative path differ by the `src/` prefix). Relative
  imports and JS/TS relative imports are unaffected. Ambiguous names are
  left `unresolved` rather than guessed at -- this is a precision/recall
  tradeoff made deliberately in favor of precision.
- Impact analysis does not detect API routes or frontend components.
- `LLMProvider.stream()` is implemented as a single-chunk wrapper around
  `generate()` for every current provider -- no real token streaming yet.
- No authentication on the API or web UI (by design, for local/single-user
  use -- see docs/security.md).
- Docker images were authored and statically validated but not built/run
  end-to-end in this environment (Docker Desktop's backend never finished
  starting here).
- The web Graph screen's edge rendering was verified structurally
  (correct data reaching React Flow) but not visually, in this
  environment's compositor-less browser pane.
