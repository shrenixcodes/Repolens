# Contributing to RepoLens

Thanks for considering a contribution. RepoLens is a Python/TypeScript
monorepo; see [`docs/development.md`](docs/development.md) for the full
local setup. This file covers the contribution workflow itself.

## Before you start

- For anything beyond a small fix, open an issue first to discuss the
  approach -- it saves everyone time if the direction doesn't fit the
  project's local-first, deterministic-first-then-AI philosophy (see the
  README's "Why it exists" section).
- Check existing issues and PRs so you're not duplicating work.

## Development setup

```bash
git clone <your-fork-url>
cd repolens
python -m venv .venv
source .venv/Scripts/activate   # Windows (git-bash); use .venv/bin/activate on macOS/Linux
pip install -e packages/shared -e packages/config -e packages/parser \
            -e packages/indexer -e packages/graph -e packages/retrieval \
            -e packages/ai -e packages/git -e apps/cli -e apps/api
pip install pytest ruff mypy

cd apps/web && npm install && cd ../..
```

## Making changes

- Keep changes focused: one logical change per pull request, matching one
  or a few related commits. Don't bundle an unrelated refactor with a
  feature or fix.
- Add or update tests for any behavior change. We don't merge untested
  behavior changes.
- Run the checks relevant to what you touched before opening a PR:

  ```bash
  # Python packages/apps
  pytest
  ruff check packages apps
  mypy packages/<name>/src/... apps/<name>/src/...

  # apps/web
  cd apps/web && npm run lint && npm run build
  ```

- Match existing code style: no comments explaining *what* code does (names
  should do that); comments only for non-obvious *why*. No speculative
  abstractions for a single current use case.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/)-style
prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`. Explain
*why* in the body when the change isn't self-evident from the diff.

## Adding language support

RepoLens's parser architecture (`packages/parser`) is pluggable by design.
To add a language:

1. Implement the `LanguageParser` protocol (`registry.py`) -- either a
   tree-sitter-backed parser (see `treesitter_parser.py` for the JS/TS/TSX
   pattern) or something else appropriate for the language.
2. Register it in `build_default_registry()`.
3. Add its extraction coverage and known limitations to
   `coverage.py` -- be honest about what isn't extracted.
4. Add fixture-based tests covering classes/functions/imports/calls at
   minimum.

## Adding a model provider

Implement the `EmbeddingProvider` or `LLMProvider` protocol in
`packages/ai`, wire it into the relevant `factory.py`, and add tests using
a mocked HTTP transport (see the existing Ollama/OpenAI-compatible provider
tests) -- no test should require a real network call or a paid API key.

## Pull requests

- Describe what changed and why, not just what.
- Link the issue it addresses, if any.
- Expect review feedback -- it's part of keeping the codebase consistent,
  not a judgment of the contribution's value.

## Reporting bugs / requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For security
issues, see [`SECURITY.md`](SECURITY.md) instead of opening a public issue.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
