# repolens-graph

Builds a repository-wide dependency/call graph from the symbols and
relationships `repolens_indexer.db.IndexStore` persisted, and answers
forward/reverse dependency queries against it.

## Cross-file resolution

Parsers (`repolens_parser`) only ever see one file, so every relationship
they record starts out `UNRESOLVED` -- the target is a name as written, not
a link to a specific symbol. `repolens_graph.resolve` is where that gets
upgraded to `RESOLVED`, using two conservative heuristics:

- **Imports**: the written module path (`./utils`, `.utils`, `a.b.c`) is
  resolved against the set of files the indexer actually found, trying the
  same extension/`__init__`/`index` conventions Python and JS/TS tooling
  use. External packages (`react`, `numpy`, ...) correctly stay unresolved
  -- they're not in the repository.
- **Calls / inheritance / implements**: the written name is looked up
  against every symbol in the repository with that exact name. If, and only
  if, exactly one candidate exists, the relationship is resolved to it. An
  ambiguous name (two classes named `Handler` in different files) is left
  unresolved rather than guessed at.

This is a name-based heuristic, not type-aware resolution -- it will not
disambiguate overloads, shadowed imports, or dynamic dispatch. Callers
(impact analysis, Q&A) must treat `UNRESOLVED` relationships as "a
plausible lead", not a confirmed edge.

## Graph shape

Nodes are files and symbols (`repolens_graph.ids`). Edges are `contains`
(file -> its symbols), plus `imports`/`calls`/`inherits`/`implements` from
the relationship table, each still carrying its `resolution` so
graph-powered features never claim unresolved guesses as confirmed facts.
