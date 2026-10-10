# repolens-ai

Provider-agnostic abstractions for the two kinds of model calls RepoLens
makes: text generation (`repolens_ai.llm`, Milestone 10) and embeddings
(`repolens_ai.embeddings`, this package's first slice).

## Embedding providers

| Provider            | Network?                 | Notes                                             |
|----------------------|---------------------------|----------------------------------------------------|
| `mock`               | none                      | deterministic hash-based vectors; default, used in tests and offline-by-default installs |
| `ollama`             | localhost (configurable)  | calls a local Ollama server's `/api/embeddings`    |
| `openai`             | api.openai.com            | requires `embedding.api_key`                       |
| `openai_compatible`  | configurable `base_url`   | any server implementing the OpenAI embeddings API (LM Studio, vLLM, text-embeddings-inference, ...) |

`EmbeddingProvider` is a small `Protocol` (`embed`, `embed_batch`) -- nothing
in `repolens_indexer` or `repolens_retrieval` imports a concrete provider
class; they're handed an object (or even just a plain function) that
satisfies the protocol. `build_embedding_provider(config)` is the one place
that turns configuration into a concrete instance.

Source code is only sent to `ollama`/`openai`/`openai_compatible` when the
user has explicitly configured one of them. The `mock` provider (the
default) never makes a network call.
