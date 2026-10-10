# Indexing

`repolens index` (or `POST /repositories/{id}/index`) runs
`repolens_indexer.pipeline.run_index`, which does, per file:

1. **Discover** -- `repolens_indexer.discovery.discover_files` walks the
   repository, applying (in order) a hard-coded secret-file exclusion list,
   `.gitignore` (if `indexing.respect_gitignore`), and `indexing.ignore`.
   Every path is validated to stay inside the repository root even through
   symlinks.
2. **Hash** -- content is hashed (`sha256`); if the hash matches what's
   already stored for that path, the file is skipped entirely (this is
   what makes re-indexing fast on a large, mostly-unchanged repository).
3. **Parse** -- if a parser is registered for the file's extension
   (`repolens_parser.build_default_registry`), it extracts symbols,
   relationships, and imports. Files with no registered parser (markdown,
   JSON, config files, ...) are still indexed -- just without symbol
   extraction.
4. **Persist** -- symbols/relationships/imports replace whatever was
   previously stored for that file (`IndexStore.replace_file_*`).
5. **Chunk** -- `repolens_indexer.chunking.build_chunks` splits the file
   into one chunk per top-level symbol (using its exact source lines), or
   one whole-file chunk if there were no symbols. Chunks are indexed into
   a SQLite FTS5 table for lexical search.
6. **Embed** *(optional)* -- if `indexing.enable_embeddings` is true and an
   embedding backend was supplied, each chunk's embedding vector is
   computed and stored.

After all files are processed, any previously-indexed file no longer found
on disk is removed from the index (cascading to its symbols,
relationships, imports, and chunks via `ON DELETE CASCADE`).

## What gets reported

`IndexResult` (`files_scanned`, `files_indexed`, `files_unchanged`,
`files_removed`, `files_failed`, `errors`) is what `repolens index --json`
and `POST /repositories/{id}/index` return. A file with a parse error
(e.g. a syntax error) still gets indexed with whatever was successfully
extracted before the error -- partial results beat discarding the whole
file, and the error is still reported in `errors`.

## Resolution happens later, not here

Indexing stores relationships exactly as the parser saw them --
`unresolved`, pointing at a name rather than a specific symbol. Turning
those into confirmed edges is `repolens_graph`'s job (see
[`packages/graph/README.md`](../packages/graph/README.md)), which runs
when a graph is actually requested (`repolens impact`, `repolens ask`, the
`/graph` endpoint, ...), not as part of indexing itself.

## Cache / state location

Everything indexing produces lives in one SQLite file:
`<repo>/.repolens/repolens.sqlite3` by default (`database.path` in
`repolens.yaml`). Delete it (or the whole `.repolens/` directory) to force
a full re-index from scratch.
