# repolens-shared

Common building blocks used by every other RepoLens package:

- `repolens_shared.exceptions` — the shared exception hierarchy.
- `repolens_shared.paths` — path-safety helpers (`resolve_within_root`) used anywhere
  a user-controlled path touches the filesystem, to prevent path-traversal escapes.
- `repolens_shared.types` — small, dependency-free dataclasses (`SourceLocation`,
  `Citation`) used across the parser, graph, retrieval, and AI layers.
- `repolens_shared.hashing` — deterministic content hashing for incremental indexing.
- `repolens_shared.logging` — logging setup that redacts secrets and never logs
  full source code bodies.

This package has no third-party dependencies by design: everything else in the
monorepo depends on it, so it must stay trivially installable.
