# repolens-indexer

File discovery, ignore-rule handling, content hashing, and the incremental
indexing pipeline.

- `repolens_indexer.discovery` — walks a repository root, applies
  `.gitignore` plus `repolens.yaml`'s `indexing.ignore` patterns, enforces a
  hard-coded secret-file exclusion list that cannot be overridden from
  config, and guarantees (via `repolens_shared.paths`) that every returned
  path stays inside the repository root even in the presence of symlinks.
- `repolens_indexer.pipeline` — orchestrates discovery -> parsing -> symbol
  storage -> relationship storage -> chunking, re-processing only files
  whose content hash changed since the last run (Milestone 6).
