# repolens-config

Layered configuration for RepoLens: built-in defaults are overridden by an
optional `repolens.yaml` file in the repository root, which is in turn
overridden by environment variables. Later layers always win.

```python
from pathlib import Path
from repolens_config import load_config

config = load_config(Path("/path/to/repo"))
print(config.llm.provider)       # "mock" by default -- no cloud API required
print(config.server.host)        # "127.0.0.1" by default -- loopback only
```

See `docs/configuration.md` at the repository root for the full file format
and the list of supported environment variables.

Never commit a `repolens.yaml` containing a real API key. Prefer the
`REPOLENS_LLM_API_KEY` / `REPOLENS_EMBEDDING_API_KEY` environment variables,
or an untracked `repolens.local.yaml` (already excluded via `.gitignore`).
