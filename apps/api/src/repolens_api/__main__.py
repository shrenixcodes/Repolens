"""Run the RepoLens API with `python -m repolens_api` or the `repolens-api` script.

Binds to 127.0.0.1 by default -- pass REPOLENS_SERVER_HOST to expose it
more broadly, and understand the consequences (the API can index and read
any directory you register) before doing so.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("REPOLENS_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("REPOLENS_SERVER_PORT", "8000"))
    uvicorn.run("repolens_api.app:create_app", factory=True, host=host, port=port)


if __name__ == "__main__":
    main()
