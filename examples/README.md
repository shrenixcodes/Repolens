# Examples

Small, real (not fabricated) fixture repositories to try RepoLens against
without pointing it at your own code first.

- [`python-project/`](python-project) -- a small auth service: classes,
  functions, imports, a test suite.
- [`typescript-project/`](typescript-project) -- a small cart/checkout UI
  slice: TS classes/interfaces/types, TSX components, cross-file imports.
- [`fullstack-project/`](fullstack-project) -- a todo-list app with a
  Python backend and a TypeScript/React frontend, demonstrating
  independent per-language dependency graphs in one repository.

Each has its own `README.md` with commands to try. General pattern:

```bash
cd examples/<name>
repolens init
repolens index
repolens status
repolens ask "..."
```
