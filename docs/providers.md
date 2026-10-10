# AI providers

RepoLens separates two kinds of model calls -- text generation
(`repolens_ai.llm`) and embeddings (`repolens_ai.embeddings`) -- each
behind its own small protocol, configured independently (`llm.*` and
`embedding.*` in `repolens.yaml`).

## `mock` (default)

Fully offline, zero setup. `MockLLMProvider.generate` returns a fixed,
honest disclaimer ("No language model is configured...") plus a count of
how many sources were included in the prompt -- it does not attempt to
simulate real AI prose. `MockEmbeddingProvider.embed` hashes tokens into a
deterministic vector, useful for exercising the retrieval pipeline in
tests without a real semantic model.

RepoLens's grounding guarantee (citations always reflect real retrieval,
never fabricated) holds regardless of which provider is configured --
including `mock` -- because it's implemented in the retrieval layer, not
delegated to the LLM.

## `ollama`

```yaml
llm:
  provider: ollama
  model: llama3.1
embedding:
  provider: ollama
  model: nomic-embed-text
```

Defaults to `http://localhost:11434`; override with `base_url`. Uses
`/api/generate` for text and `/api/embed` for embeddings. No API key.

## `openai`

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
```

```bash
export REPOLENS_LLM_API_KEY=sk-...
```

Defaults to `https://api.openai.com/v1`. Uses the standard
`/chat/completions` and `/embeddings` endpoints.

## `openai_compatible`

Same request/response shape as `openai`, but `base_url` is required --
this is how RepoLens talks to self-hosted servers (LM Studio, vLLM,
text-embeddings-inference, or any OpenAI-API-shaped gateway):

```yaml
llm:
  provider: openai_compatible
  model: whatever-your-server-calls-it
  base_url: http://localhost:1234/v1
```

## Error handling

Every provider raises `repolens_shared.exceptions.ProviderError` on
failure (connection error, non-2xx response, unexpected response shape) --
callers never see a provider-specific exception type. A `stream()` method
exists on `LLMProvider` for interface parity with the product's streaming
ambitions, but every current provider implements it as a single-chunk
wrapper around `generate()` -- true incremental token streaming is a
documented follow-up, not something silently claimed as done.

## Adding a provider

See the "Adding a model provider" section of
[`CONTRIBUTING.md`](../CONTRIBUTING.md).
