# repolens-cli

The `repolens` command-line interface. Commands are added incrementally as
their backing functionality lands in `packages/*` -- this CLI never ships a
command that prints placeholder output instead of calling real code.

Currently available:

```
repolens --help
repolens --version
repolens doctor
```

See the root `PLAN.md` for which commands land in which milestone.
