# Example: fullstack-project

A tiny todo-list app with a Python backend (`backend/`) and a TypeScript/
React frontend (`frontend/`), demonstrating independent per-language
dependency graphs in one repository.

```bash
cd examples/fullstack-project
repolens init
repolens index
repolens ask "How are todos stored?"
repolens impact backend/app/store.py
repolens impact frontend/src/api.ts
```

Note on cross-language relationships: RepoLens's dependency graph connects
same-language imports/calls (Python-to-Python, TS-to-TS) -- it does not
automatically infer that `frontend/src/api.ts`'s `fetch("/api/todos")`
calls `backend/app/routes.py`'s `handle_list_todos`. That link exists only
in the route string itself; detecting it would require route-table
analysis RepoLens doesn't implement yet (see the README's "Known
limitations" section). Lexical search (`repolens search "todos"`) will
still surface both sides.
