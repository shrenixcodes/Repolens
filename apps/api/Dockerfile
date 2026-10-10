# Multi-stage build: compile dependencies (some, e.g. tree-sitter bindings,
# may need a toolchain) in `builder`, then copy only the resulting venv into
# a slim runtime image so the final image doesn't carry build tools.

FROM python:3.12-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY packages/shared packages/shared
COPY packages/config packages/config
COPY packages/parser packages/parser
COPY packages/indexer packages/indexer
COPY packages/graph packages/graph
COPY packages/retrieval packages/retrieval
COPY packages/ai packages/ai
COPY packages/git packages/git
COPY apps/api apps/api

# Order matters: each package's local-path dependency on an earlier one is
# satisfied by installing them left-to-right in one resolver pass.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        ./packages/shared \
        ./packages/config \
        ./packages/parser \
        ./packages/indexer \
        ./packages/graph \
        ./packages/retrieval \
        ./packages/ai \
        ./packages/git \
        ./apps/api

FROM python:3.12-slim AS runtime

# git is a runtime dependency, not just a build one: repolens-git shells out
# to the real `git` binary for history/blame.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 repolens

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Bind to all interfaces *inside the container* -- the host-side exposure is
# controlled by docker-compose's port mapping (127.0.0.1:8000:8000 by
# default), not by this container-internal bind address.
ENV REPOLENS_SERVER_HOST=0.0.0.0
ENV REPOLENS_SERVER_PORT=8000

USER repolens
WORKDIR /home/repolens
EXPOSE 8000

CMD ["python", "-m", "repolens_api"]
