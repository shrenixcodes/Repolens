# repolens-web

The RepoLens web dashboard (Next.js App Router, TypeScript, Tailwind CSS).
Talks to `repolens-api` over HTTP -- it has no server-side logic of its own,
no database access, and does not read the filesystem directly; every screen
is backed by a real API call, never fabricated/demo data.

## Running

```bash
npm install
npm run dev
```

Requires the API running at `http://127.0.0.1:8000` (see `apps/api/README.md`).
Override the API location with `NEXT_PUBLIC_API_BASE_URL` (see `.env.local`).

## Screens

- **Dashboard** (`/`) -- index status, language/symbol-kind breakdown, re-index trigger.
- **Explorer** (`/explorer`) -- browse indexed files, view source with line numbers and extracted symbols.
- **Search** (`/search`) -- lexical search over indexed chunk content.
- **Ask** (`/ask`) -- grounded repository Q&A with citations and related symbols.
- **Graph** (`/graph`) -- interactive dependency graph (React Flow): pan/zoom, node-type filtering, text filtering, click-to-inspect, and a shortcut into Impact analysis for the selected node.
- **Impact** (`/impact`) -- direct/transitive dependents, related tests, and stated analysis limitations for a file or `path::symbol` target.
- **History** (`/history`) -- real Git commit history for a file.

## Design

Dark-first, information-dense, monospace-accented -- styled to read like a
developer tool (terminal, editor, GitHub), not a marketing site. See
`src/app/globals.css` for the color tokens.

## Known limitation

The repository registry (`apps/api`) is a single shared list; this UI does
not yet support per-user workspaces or auth -- it's built for local,
single-user use, consistent with the rest of RepoLens's local-first design.
