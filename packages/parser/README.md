# repolens-parser

Pluggable source-code parsing. Each language implements the `LanguageParser`
protocol (`registry.py`) and produces a `ParseResult`: a list of symbols
(classes, functions, methods, interfaces, type aliases, top-level
variables), relationships (imports, calls, inheritance, implementation --
each tagged with a `ResolutionStatus` since cross-file resolution happens
later, in the indexer/graph layer, not here), and raw imports.

## Supported languages (MVP)

| Language              | Backend          | Extracted                                                              |
|------------------------|------------------|-------------------------------------------------------------------------|
| Python                 | stdlib `ast`     | classes, functions, methods, imports, calls, inheritance, docstrings, decorators |
| JavaScript / JSX       | tree-sitter      | classes, functions, methods, imports, calls, inheritance                |
| TypeScript / TSX       | tree-sitter      | the above, plus interfaces, type aliases, `implements`                  |

## Known limitations

- Relationships extracted here are **not** resolved across files. A `CALLS`
  relationship records the callee name as written in the source
  (`resolution=UNRESOLVED`); turning that into an edge to a specific symbol
  in another file is the job of `repolens_graph`, which has visibility into
  the whole repository.
- JS/TS docstrings (JSDoc comments) are not extracted yet.
- Destructured imports re-exported with `export { x } from './y'` are not
  distinguished from local re-exports.
- Dynamic `import()` calls and `require()` calls are not tracked as imports.

Call `repolens_parser.coverage.describe_coverage()` to get this list
programmatically -- the CLI and web UI surface it so users know what the
tool actually understood versus guessed.
