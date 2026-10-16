# Run and share ANDOLAN

The repository now implements **City Reform Beta 0.3**: five repeatable city jobs, five linked cases, a persistent crew mandate and the separate original six-chapter Story. Final 0.3 verification and publication are pending. The public site at [occult-kranti.github.io/ANDOLAN](https://occult-kranti.github.io/ANDOLAN/) still serves **First Edition 0.1**; its successful release evidence is retained below.

The full six-district, 22-mission production and an operated multiplayer service remain separate milestones. Provider-neutral Docker/Compose files and a prepared paid [Render Blueprint](../render.yaml) are available; [the Render guide](MULTIPLAYER_HOSTING.md) explains the unexecuted deployment. No multiplayer hosting account, purchase, service or domain has been created.

## Try the downloadable solo game

Run `npm run build:standalone`. The resulting `dist/standalone/index.html` contains the code, styles, fonts, procedural audio and third-party notices for City practice and Story. Use a current Chromium browser with WebGL2. You can open the downloaded HTML directly where local-file navigation is allowed, or serve its folder with `python3 -m http.server 8080` and open it through that local server.

This environment's managed Chromium blocks direct `file://` navigation. The **First Edition 0.1** self-contained build was verified over HTTP, then with networking disabled for Story dialogue, vehicle entry and driving, without external asset requests or page errors; save detection after reload also passed. Those historical results are in `evidence/production-browser-final-check.json` and the earlier invite check in `evidence/production-browser-check.json`. They do not establish the final Beta 0.3 artifact's verification, which remains pending.

City practice and Story run entirely on that device and use separate browser saves. Browser private mode, clearing site data, or moving the file to another origin can remove or separate saves. Multiplayer requires the game server described below.

The static build is also suitable for an HTTPS static host. In the beta lobby, **Game server address** accepts the actual server's HTTPS or WSS URL at runtime; no client rebuild is needed. `VITE_SERVER_URL` remains an optional build-time default. Neither value is a credential. Without a server, choose **City practice** or **Begin/Continue story**. Online entry reports unsuccessful connections instead of simulating other humans.

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

The compiled Node service serves `dist/client`, WebSocket `/ws`, and health `/health` on `PORT` (default 3001). Keep `ANDOLAN_DATA_DIR` on persistent writable storage. `.data` is deliberately excluded from Git. The process handles SIGTERM by checkpointing rooms and closing transports. Beta 0.3 speaks **protocol 2**; update client and server together. A healthy protocol-one server is not compatible with this client.

For a container, build the included Dockerfile, or run `docker compose up --build`. Compose targets `andolan:0.3` and retains saves in a named volume. The final 0.3 container build/restart check is pending. Terminate HTTPS in the hosting provider or a reverse proxy that supports WebSocket upgrades. The process must remain running: a static host alone cannot provide live rooms.

Do not map the development sandbox directly to an unrestricted public matchmaking service. It currently has preset signals, safe name rendering, limited rooms, bounded message rates and private/public separation. It does not yet have accounts, operational reporting/blocking/moderation, geographic matchmaking or a production economy. Private invited testing is the intended deployment audience.

## Backups and rollback

Back up the persistent data directory after a graceful stop, or use an application-consistent volume snapshot. Room files are written by temporary file plus atomic rename. They contain room progress and hashed reconnection identities; do not publish them with the client. Keep the deployment image and content version beside each backup.

The 0.3 implementation migrates supported simulation schemas **1 and 2 to 3**, retaining existing Story progress, active jobs/cargo, shared counters and reconnection identities. The new city-case ledger starts empty; earlier repeatable-job receipts do not invent completed sector cases. Before upgrading a server room, it preserves the original file as `<room>.json.legacy-v1.bak` or `.legacy-v2.bak` without overwriting an existing backup. Invalid or unsupported saves are rejected; this is not a general migration for arbitrary versions. The final release verification must include migration/reconnect checks before rollout.

For rollback, stop the replacement process, restore its matching prior image and backed-up data, then verify `/health` and a private reconnect. Never overwrite a newer campaign checkpoint without preserving it.

## ChatGPT testing

This chat's exposed tools support shell execution and local Chromium testing. They do not expose an interactive game canvas, Sites publisher, public tunnel or deployment connector. A game cannot be claimed to run inside ChatGPT from a screenshot. The deliverables are a public solo website, a standalone browser HTML file and deployable client/server source. Whether an external hosted game can be embedded in a particular ChatGPT surface depends on that surface's capabilities and policy; no embedded run has been verified here.

## Costs and capacity

No hosting purchase has been made and no monthly cost is asserted. A local 16-WebSocket synthetic measurement is recorded in `../tests/network-benchmark.json`; it does not establish regional or sustained capacity. Choose a provider and quote against actual concurrent rooms, CPU/memory, asset traffic and persistent storage after invited device playtests. The initial client bundle is measured by the build output, rather than estimated as a large-world asset budget.

## Managed build proxies

This cloud uses a managed HTTPS proxy with an additional public CA bundle. The container base image does not initially trust that CA. The Dockerfile supports an optional BuildKit secret `registry_ca`; supply the environment-provided public certificate bundle for dependency installation. Use the existing `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` bindings as build arguments when required. The trust bundle is mounted only during build steps and is not copied into the runtime image. TLS verification and lockfile integrity remain enabled. Ordinary hosts using public registry certificates do not need this optional secret.

`python tools/cloud/build-container.py` supplies these existing bindings and resolves the proxy hostname for BuildKit, whose DNS differed from the shell in this workspace. It does not print proxy credentials, change the proxy, or disable certificate checks. If Docker's default configuration directory is read-only here, use `DOCKER_CONFIG=/workspace/tooling/docker python tools/cloud/build-container.py`. After the current managed build completes, `docker compose up --no-build` uses `andolan:0.3`; keep the same `DOCKER_CONFIG` override when required. The tag/configuration change alone does not establish a passed container check.

## GitHub Pages release status and history

`.github/workflows/pages.yml` verifies TypeScript, lint, unit/network/content tests and Chromium browser tests, builds the single-file browser game, and publishes it on pushes to `main`. The full campaign browser gate takes several minutes. The repository is now configured to use GitHub Actions for Pages.

**Beta 0.3 publication is pending.** When published, Pages will host local City practice/Story and the client that can connect to a separately hosted protocol-two server. Pages itself cannot host the WebSocket service.

**First Edition 0.1 historical release:** [https://occult-kranti.github.io/ANDOLAN/](https://occult-kranti.github.io/ANDOLAN/) currently offers the original **Story** preview. Run [38846677208](https://github.com/occult-kranti/ANDOLAN/actions/runs/38846677208), on `a0e9f1cc413b6fefcbff46337cbd784d37b4a798`, passed source checks, all 51 tests, seven browser cases (6.8 minutes), production builds and deployment. At that check, the public HTTPS response was 200 and its 2,374,537-byte HTML matched the locally verified standalone SHA-256. Evidence remains in `evidence/github-pages-release-run.json` and `evidence/public-pages-http-check.json`. No WebSocket backend was deployed with that release.

That release's live public Chromium check also passed: keyboard dialogue, vehicle entry/exit, 11.86 m driving, journal access, exact saved stage/position restoration and persisted camera comfort. There were no page/console errors, failed HTTP requests or external asset requests. See `evidence/public-pages-browser-check.json` and `evidence/public-pages-story.png`. The initial cloud-only certificate-store restriction and its scoped resolution are retained in `evidence/public-pages-cloud-browser-check.json`; TLS validation remained enabled. This was a public solo smoke check, not a second full campaign traversal or a hosted multiplayer test.

Earlier attempts remain part of the release history. Initial network checks were blocked; later API reads worked, but Pages was disabled, its settings/read and create requests returned **HTTP 403, Resource not accessible by integration**, and the intended site returned 404. Run [38837936134](https://github.com/occult-kranti/ANDOLAN/actions/runs/38837936134) passed source checks, 51 tests, seven browser cases and production builds, then failed at Pages configuration with `Not Found`; deployment was skipped. The user subsequently enabled Pages, allowing the new workflow to publish. The earlier failures do not describe the current website's availability.

The environment draft adds `api.github.com`, `occult-kranti.github.io`, `uploads.github.com` (release assets) and `results-receiver.actions.githubusercontent.com` (Actions logs) and saves the installation/start instructions. The draft save itself does not confirm activation or a published snapshot: review and save the environment settings, then publish the environment. No additional secret is required for the game itself.
