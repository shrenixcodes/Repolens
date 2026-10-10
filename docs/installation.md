# Installation

## Requirements

- Python 3.10+
- Node.js 20+ (only needed for the web dashboard)
- `git` (needed for `repolens history`/blame; optional otherwise)
- Optional: [Ollama](https://ollama.com) for local models, or an OpenAI
  (-compatible) API key for cloud models

## CLI only

```bash
git clone https://github.com/shrenixcodes/Repolens.git
cd Repolens

python -m venv .venv
source .venv/Scripts/activate   # Windows (git-bash) -- .venv/bin/activate on macOS/Linux

pip install -e packages/shared -e packages/config -e packages/parser \
            -e packages/indexer -e packages/graph -e packages/retrieval \
            -e packages/ai -e packages/git -e apps/cli
```

This installs each package in editable mode, in dependency order (each
later package's local-path dependency on an earlier one is satisfied by
the one already installed). Verify with:

```bash
repolens --version
repolens doctor
```

## + HTTP API

```bash
pip install -e apps/api
python -m repolens_api
```

Binds to `127.0.0.1:8000` by default. Override with
`REPOLENS_SERVER_HOST`/`REPOLENS_SERVER_PORT`.

## + Web dashboard

```bash
cd apps/web
npm install
cp .env.example .env.local   # defaults to http://127.0.0.1:8000
npm run dev
```

Open `http://localhost:3000`.

## Docker

```bash
docker compose up --build
```

See the [Docker section of the README](../README.md#docker) and the
comments in [`docker-compose.yml`](../docker-compose.yml) for how to mount
the repositories you want to index.

## Verifying your install

```bash
cd /path/to/any/git/repository
repolens init
repolens index
repolens status
repolens ask "What does this repository do?"
```

With no model configured, `ask` still returns real retrieved evidence --
see the [Local model setup](../README.md#local-model-setup-ollama) and
[Cloud model setup](../README.md#cloud-model-setup) sections of the README
for a natural-language answer.

## Troubleshooting

- `repolens doctor` checks Python version, `git` availability, SQLite, and
  config loading, and explains how to fix anything it finds broken.
- If a package fails to install because of a missing compiler toolchain,
  it's almost always a tree-sitter grammar package needing to build from
  source because no prebuilt wheel exists for your platform/Python
  version -- try a Python version with broader wheel support (3.11/3.12
  are well covered as of this writing).
