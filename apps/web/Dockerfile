# Build context must be the repository root (see docker-compose.yml) --
# `next.config.ts` sets output: "standalone" so the runtime stage only
# needs the pruned server bundle, not the full node_modules tree.

FROM node:22-slim AS builder
WORKDIR /build/apps/web

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

COPY apps/web ./

# NEXT_PUBLIC_* values are baked in at build time, not read at container
# start -- this must be the URL the *browser* (running on the host, not
# inside the Docker network) will use to reach the API.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build

FROM node:22-slim AS runtime
RUN useradd --create-home --uid 1000 repolens
WORKDIR /home/repolens/app

COPY --from=builder /build/apps/web/.next/standalone ./
COPY --from=builder /build/apps/web/.next/static ./.next/static
COPY --from=builder /build/apps/web/public ./public

USER repolens
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
EXPOSE 3000

CMD ["node", "server.js"]
