# Example: python-project

A tiny, runnable auth service (registration, login, token verification)
demonstrating classes, functions, imports, inheritance-free composition,
and a test suite RepoLens can use for impact analysis's "related tests".

```bash
cd examples/python-project
repolens init
repolens index
repolens ask "How does login work?"
repolens search "verify token"
repolens impact app/security.py
repolens impact app/auth.py::AuthService.login
```

Try changing `app/security.py` and re-running `repolens impact app/security.py`
-- you should see `app/auth.py` and `tests/test_auth.py` as dependents.
