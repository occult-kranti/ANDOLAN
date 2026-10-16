FROM node:24-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS build
WORKDIR /app
ENV NODE_USE_ENV_PROXY=1
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=registry_ca \
    if [ -f /run/secrets/registry_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/registry_ca; fi; \
    npm ci --strict-ssl=true --cache=/tmp/yuga-npm --fetch-timeout=30000 --fetch-retries=1
COPY tsconfig.server.json tsconfig.yuga.server.json vite.yuga.config.ts THIRD_PARTY_NOTICES.md ./
COPY games/yuga ./games/yuga
RUN --mount=type=secret,id=registry_ca \
    if [ -f /run/secrets/registry_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/registry_ca; fi; \
    npm run yuga:build && npm prune --omit=dev --strict-ssl=true --cache=/tmp/yuga-npm --fetch-timeout=30000 --fetch-retries=1

FROM node:24-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5
WORKDIR /app
ENV NODE_ENV=production PORT=3005
COPY --from=build --chown=node:node /app/package.json ./package.json
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist/yuga ./dist/yuga
COPY --from=build --chown=node:node /app/dist/yuga-server ./dist/yuga-server
USER node
EXPOSE 3005
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD node -e "fetch('http://127.0.0.1:'+process.env.PORT+'/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "dist/yuga-server/games/yuga/server/index.js"]
