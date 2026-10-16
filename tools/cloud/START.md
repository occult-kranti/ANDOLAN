# Start ANDOLAN in the cloud environment

Use the existing isolated `/workspace/ANDOLAN` checkout. Preserve its working changes and saved games. The install script is `bash tools/cloud/setup.sh`; it installs the pinned lockfile and compiles the browser client and Node server.

1. Check whether ports 5173 and 3001 already belong to this project. Reuse a running development process when healthy; avoid duplicate watchers.
2. From the checkout, run `npm run dev` in a persistent execution session. The Vite client listens on 5173, with `/ws` and `/health` proxied to the server on 3001.
3. Verify the local `/health` response and browser title before editing. Use internal browser tooling for testing. The current ChatGPT surface does not provide a public preview tunnel or embedded game canvas; do not present loopback addresses as user-accessible links.
4. Run `npm run typecheck`, `npm run lint` and `npm test` for verification. `npm run test:e2e` uses Chromium; set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` if it is installed elsewhere. Keep source files stable during full campaign and multiplayer browser checks.
5. `npm run build:standalone` creates the downloadable solo game. `npm run build && npm start` serves the production client and WebSocket server together. Persistent room saves live in `.data` unless `ANDOLAN_DATA_DIR` is set.

No API key is needed to play or build. REA is an optional research tool, already exercised for the original vehicle contract; restoration instructions are in `docs/research/REA_RUNBOOK.md`. Docker and hosting are optional deployment paths, described in `docs/DEPLOYMENT.md`.
