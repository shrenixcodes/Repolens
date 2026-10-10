# repolens-retrieval

Combines the three retrieval signals the product vision calls for, instead
of leaning on vector similarity alone:

1. **Lexical** -- `repolens_indexer.search_lexical` (FTS5 over chunk content).
2. **Semantic** -- `repolens_indexer.semantic_search` (cosine over stored
   embeddings), only when an embedding function is supplied -- retrieval
   degrades to lexical-only when no model is configured, it never fails.
3. **Structural** -- a fixed boost when the query literally names a
   symbol's bare identifier, using the same repository graph
   `repolens_graph` builds.

`hybrid_search` min-max normalizes each signal's scores *within the current
result set* before combining them (there's no universal lexical-vs-cosine
scale to calibrate against), then returns one ranked, deduplicated list
with each result's contributing sources so callers (and the web UI) can
show *why* something ranked where it did.

`expand_with_graph` pulls in directly-connected symbols (one hop: callers,
callees, imports) around a set of seed results, for callers that want
"what else is relevant to this answer" without re-running search.

`assemble_context` trims a ranked result list to a character budget,
highest-scored first -- the context an LLM prompt actually gets is capped,
not "every match concatenated."
