# Run and share ANDOLAN

The current release is **First Edition 0.1**, a condensed six-mission playable preview. The full six-district, 22-mission production and an operated public service are separate roadmap milestones. The user selected provider-neutral deployment files; no provider account, purchased service or domain has been created.

## Try the downloadable solo game

Run `npm run build:standalone`. The resulting `dist/standalone/index.html` contains the game code, styles, fonts and third-party notices. Use a current Chromium browser with WebGL2. You can open the downloaded HTML directly where local-file navigation is allowed, or serve its folder with `python3 -m http.server 8080` and open it through that local server. This environment's managed Chromium blocks direct `file://` navigation; the self-contained build was verified over HTTP, then with networking disabled for Story dialogue, vehicle entry and driving. No external asset requests or page errors occurred. Save detection after reload also passed. See `evidence/production-browser-check.json`.

Story runs entirely on that device and stores its checkpoint in browser local storage. Browser private mode, clearing site data, or moving the file to another origin can remove or separate saves. Multiplayer requires the game server described below.

The static build is also suitable for an HTTPS static host. `VITE_SERVER_URL` can point a separately hosted client at a WSS game server at build time. Do not send credentials in this variable. Without a server, use Story; the UI reports unsuccessful online connections instead of simulating other humans.

## Develop in this cloud workspace

Use `/workspace/ANDOLAN` directly. This cloud task is already isolated; no worktree is required.

```sh
npm ci
npm run dev
```

The development client uses port 5173 and proxies `/ws` and `/health` to the room service on port 3001. The browser uses PlayCanvas; no graphics engine editor or external game assets are needed. REA is an optional external research tool; see `research/REA_RUNBOOK.md`.

## One process deployment

```sh
npm ci
npm run build
npm start
```

The compiled Node service serves `dist/client`, WebSocket `/ws`, and health `/health` on `PORT` (default 3001). Keep `ANDOLAN_DATA_DIR` on persistent writable storage. `.data` is deliberately excluded from Git. The process handles SIGTERM by checkpointing rooms and closing transports.

For a container, build the included Dockerfile, or run `docker compose up --build`. The compose file retains saves in a named volume. Terminate HTTPS in the hosting provider or a reverse proxy that supports WebSocket upgrades. The process must remain running: a static host alone cannot provide live rooms.

Do not map the development sandbox directly to an unrestricted public matchmaking service. It currently has preset signals, safe name rendering, limited rooms, bounded message rates and private/public separation. It does not yet have accounts, operational reporting/blocking/moderation, geographic matchmaking or a production economy. Private invited testing is the intended deployment audience.

## Backups and rollback

Back up the persistent data directory after a graceful stop, or use a volume snapshot. Room files are written by temporary file plus atomic rename. They contain private story progress and hashed reconnection identities; do not publish them with the client. Keep the deployment image and content version beside each backup. Saves with incompatible schema/content versions are rejected rather than silently interpreted. A content-version change requires a tested migration before rollout; none is claimed in this release.

For rollback, stop the replacement process, restore its matching prior image and backed-up data, then verify `/health` and a private reconnect. Never overwrite a newer campaign checkpoint without preserving it.

## ChatGPT testing

This chat's exposed tools support shell execution and local Chromium testing. They do not expose an interactive game canvas, Sites publisher, public tunnel or deployment connector. A game cannot be claimed to run inside ChatGPT from a screenshot. The deliverables are a standalone browser HTML file and deployable client/server. Whether an external hosted game can be embedded in a particular ChatGPT surface depends on that surface's capabilities and policy; no embedded run has been verified here.

## Costs and capacity

No hosting purchase has been made and no monthly cost is asserted. A local 16-WebSocket synthetic measurement is recorded in `../tests/network-benchmark.json`; it does not establish regional or sustained capacity. Choose a provider and quote against actual concurrent rooms, CPU/memory, asset traffic and persistent storage after invited device playtests. The initial client bundle is measured by the build output, rather than estimated as a large-world asset budget.

## Managed build proxies

This cloud uses a managed HTTPS proxy with an additional public CA bundle. The container base image does not initially trust that CA. The Dockerfile supports an optional BuildKit secret `registry_ca`; supply the environment-provided public certificate bundle for dependency installation. Use the existing `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` bindings as build arguments when required. The trust bundle is mounted only during build steps and is not copied into the runtime image. TLS verification and lockfile integrity remain enabled. Ordinary hosts using public registry certificates do not need this optional secret.

`python tools/cloud/build-container.py` supplies these existing bindings and resolves the proxy hostname for BuildKit, whose DNS differed from the shell in this workspace. It does not print proxy credentials, change the proxy, or disable certificate checks. If Docker's default configuration directory is read-only here, use `DOCKER_CONFIG=/workspace/tooling/docker python tools/cloud/build-container.py`. After this managed build, `docker compose up --no-build` uses the resulting `andolan:0.1` image; keep the same `DOCKER_CONFIG` override when required.

## GitHub Pages release

`.github/workflows/pages.yml` verifies TypeScript, lint, unit/network/content tests and Chromium browser tests, builds the single-file browser game, and publishes it on pushes to `main`. The full campaign browser gate takes several minutes. In repository **Settings → Pages**, choose **GitHub Actions** as the source before the first deployment. The workflow has repository content read permission and Pages deployment permission; it cannot enable Pages administration on its own.

The intended address is `https://occult-kranti.github.io/ANDOLAN/`. Treat it as a target until a successful Actions deployment and an HTTP/browser check confirm it. Static Pages hosting supports solo Story; an independently hosted WebSocket service is still required for online rooms.

The current cloud network blocks the GitHub API and Pages hostname. An environment draft adds exactly `api.github.com` and `occult-kranti.github.io` and saves the installation/start instructions. Saving a draft does not activate it: review and save the environment settings, then publish the environment. No additional secret is required for the game itself.
