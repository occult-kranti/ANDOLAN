# Run and share ANDOLAN

**City Reform Beta 0.3 is published** at [occult-kranti.github.io/ANDOLAN](https://occult-kranti.github.io/ANDOLAN/): five repeatable city jobs, five linked cases, a persistent crew mandate and the separate original Story. Release `c20e912c789958d60581891f7c224bf0c7573f6b` passed 134 tests, typecheck/lint, all thirteen CI browser cases (11.8 minutes), builds and deployment. Both public URL checks match the exact local standalone HTML; the native live-site smoke passed in 28.889 seconds with no browser or request errors.

Its application/build inputs are identical to `b02d96f4947c0f0284d9bfcf64486bff80d7e770`, the revision used for the recorded production builds and container migration/restart. The intervening change affects test synchronization only. First Edition 0.1 evidence remains historical below; it no longer describes the currently served version.

The full six-district, 22-mission production and an operated multiplayer service remain separate milestones. Provider-neutral Docker/Compose files and a prepared paid [Render Blueprint](../render.yaml) are available; [the Render guide](MULTIPLAYER_HOSTING.md) explains the unexecuted deployment. No multiplayer hosting account, purchase, service or domain has been created.

## Try the downloadable solo game

Run `npm run build:standalone`. The resulting `dist/standalone/index.html` contains the code, styles, fonts, procedural audio and third-party notices for City practice and Story. Use a current Chromium browser with WebGL2. You can open the downloaded HTML directly where local-file navigation is allowed, or serve its folder with `python3 -m http.server 8080` and open it through that local server.

This environment's managed Chromium blocks direct `file://` navigation. The **First Edition 0.1** self-contained build was verified over HTTP, then with networking disabled for Story dialogue, vehicle entry and driving, without external asset requests or page errors; save detection after reload also passed. Those historical results remain in `evidence/production-browser-final-check.json` and `evidence/production-browser-check.json`. Beta 0.3's standalone build, public exact-byte comparison and native live-site check pass. The 0.3 check restored practice progress/settings after reload, then continued practice and a separate Story interaction in an already-loaded offline tab with zero new requests. It did not test offline navigation or installation. See `evidence/city-reform-public-browser.json`.

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

For a container, build the included Dockerfile, or run `docker compose up --build`. Compose targets `andolan:0.3` and retains saves in a named volume. The final local 0.3 container passed as non-root `node`: health/protocol 2, production HTML, real old-room migration, two WebSocket clients, ordinary movement through the first media briefing and graceful restart preserving the next stage. See [city-reform-container-check.json](evidence/city-reform-container-check.json). This does not establish full sector traversal or an operated public backend. Terminate HTTPS in the provider or a reverse proxy supporting WebSocket upgrades; a static host alone cannot provide live rooms.

Do not map the development sandbox directly to an unrestricted public matchmaking service. It currently has preset signals, safe name rendering, limited rooms, bounded message rates and private/public separation. It does not yet have accounts, operational reporting/blocking/moderation, geographic matchmaking or a production economy. Private invited testing is the intended deployment audience.

## Backups and rollback

Back up the persistent data directory after a graceful stop, or use an application-consistent volume snapshot. Room files are written by temporary file plus atomic rename. They contain room progress and hashed reconnection identities; do not publish them with the client. Keep the deployment image and content version beside each backup.

The 0.3 implementation migrates supported simulation schemas **1 and 2 to 3**, retaining existing Story progress, active jobs/cargo, shared counters and reconnection identities. The new city-case ledger starts empty; earlier repeatable-job receipts do not invent completed sector cases. Before upgrading a server room, it preserves the original file as `<room>.json.legacy-v1.bak` or `.legacy-v2.bak` without overwriting an existing backup. Invalid or unsupported saves are rejected; this is not a general migration for arbitrary versions.

The final container check used a copied persistent volume from an actual 0.2 server. Schema-two migration preserved the bound job and bearer identity, retained both the original volume and source-room backup, and wrote schema three. Two real clients then began the media case; a graceful 0.3 restart restored `archive-load`. Keep operator backups even with this automatic legacy copy.

For rollback, stop the replacement process, restore its matching prior image and backed-up data, then verify `/health` and a private reconnect. Never overwrite a newer campaign checkpoint without preserving it.

## ChatGPT testing

This chat's exposed tools support shell execution and local Chromium testing. They do not expose an interactive game canvas, Sites publisher, public tunnel or deployment connector. A game cannot be claimed to run inside ChatGPT from a screenshot. The deliverables are a public solo website, a standalone browser HTML file and deployable client/server source. Whether an external hosted game can be embedded in a particular ChatGPT surface depends on that surface's capabilities and policy; no embedded run has been verified here.

## Costs and capacity

No hosting purchase has been made and no monthly cost is asserted. A local 16-WebSocket synthetic measurement is recorded in `../tests/network-benchmark.json`; it does not establish regional or sustained capacity. Choose a provider and quote against actual concurrent rooms, CPU/memory, asset traffic and persistent storage after invited device playtests. The initial client bundle is measured by the build output, rather than estimated as a large-world asset budget.

## Managed build proxies

This cloud uses a managed HTTPS proxy with an additional public CA bundle. The container base image does not initially trust that CA. The Dockerfile supports an optional BuildKit secret `registry_ca`; supply the environment-provided public certificate bundle for dependency installation. Use the existing `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` bindings as build arguments when required. The trust bundle is mounted only during build steps and is not copied into the runtime image. TLS verification and lockfile integrity remain enabled. Ordinary hosts using public registry certificates do not need this optional secret.

`python tools/cloud/build-container.py` supplies these existing bindings and resolves the proxy hostname for BuildKit, whose DNS differed from the shell in this workspace. It does not print proxy credentials, change the proxy, or disable certificate checks. If Docker's default configuration directory is read-only here, use `DOCKER_CONFIG=/workspace/tooling/docker python tools/cloud/build-container.py`. The completed managed build produced `andolan:0.3`; `docker compose up --no-build` uses that tag. Keep the same `DOCKER_CONFIG` override when required. The exact checked image ID and source revision are in the container evidence.

## GitHub Pages release status and history

`.github/workflows/pages.yml` verifies TypeScript, lint, unit/network/content tests and Chromium browser tests, builds the single-file browser game, and publishes it on pushes to `main`. The full campaign browser gate takes several minutes. The repository is now configured to use GitHub Actions for Pages.

**Beta 0.3 published successfully.** [Run 38857615158](https://github.com/occult-kranti/ANDOLAN/actions/runs/38857615158), on `c20e912c789958d60581891f7c224bf0c7573f6b`, passed source checks, 134 tests, thirteen browser cases (11.8 minutes), both production builds and Pages deployment. The bare public URL and a release-query URL returned HTTP 200 with the exact 2,478,963-byte local standalone file: SHA-256 `fa3e602d80168c2334741a5834a27d66f3998c49b1f3f99cb3b7d47ff6bd0c4b`. See [release-run evidence](evidence/city-reform-pages-run.json) and [public HTTP evidence](evidence/city-reform-public-http.json). The native live-site check passed in 28.889 seconds: visible UI/keyboard earned a recovery pickup, drove and braked, restored saved state/settings and continued local play in an already-loaded offline tab. See [public browser evidence](evidence/city-reform-public-browser.json).

The first full [run 38855475148](https://github.com/occult-kranti/ANDOLAN/actions/runs/38855475148), on `b02d96f4947c0f0284d9bfcf64486bff80d7e770`, passed twelve browser cases and failed the van-entry assertion in the thirteenth (11.2 minutes); deployment was skipped. The original cause remains unproven. The unchanged walking/entry path passed locally before the test change, so this is not evidence of a reproduced or repaired gameplay defect.

Release `c20e912c789958d60581891f7c224bf0c7573f6b` adds an authoritative neutral-input acknowledgement and radius check to the browser harness. It retains the native entry action and existing timeouts. Targeted van/media routes passed in 95.940 / 71.083 seconds; typecheck and targeted lint passed. [The barrier evidence](evidence/city-reform-walk-barrier-check.json) records the original uncertainty and the change's limits. Application/build inputs are unchanged, so the recorded production/standalone/container artifacts remain valid for the same game code. The replacement complete run subsequently passed as recorded above.

Pages now hosts local City practice/Story and the client that can connect to a separately hosted protocol-two server. Pages itself cannot host the WebSocket service; no public multiplayer backend has been provisioned.

**First Edition 0.1 historical release:** run [38846677208](https://github.com/occult-kranti/ANDOLAN/actions/runs/38846677208), on `a0e9f1cc413b6fefcbff46337cbd784d37b4a798`, published the original Story preview after passing source checks, all 51 tests, seven browser cases (6.8 minutes) and builds. At that check, the public HTTPS response was 200 and its 2,374,537-byte HTML matched the locally verified standalone SHA-256. Evidence remains in `evidence/github-pages-release-run.json` and `evidence/public-pages-http-check.json`. No WebSocket backend was deployed with that release.

That release's live public Chromium check also passed: keyboard dialogue, vehicle entry/exit, 11.86 m driving, journal access, exact saved stage/position restoration and persisted camera comfort. There were no page/console errors, failed HTTP requests or external asset requests. See `evidence/public-pages-browser-check.json` and `evidence/public-pages-story.png`. The initial cloud-only certificate-store restriction and its scoped resolution are retained in `evidence/public-pages-cloud-browser-check.json`; TLS validation remained enabled. This was a public solo smoke check, not a second full campaign traversal or a hosted multiplayer test.

Earlier attempts remain part of the release history. Initial network checks were blocked; later API reads worked, but Pages was disabled, its settings/read and create requests returned **HTTP 403, Resource not accessible by integration**, and the intended site returned 404. Run [38837936134](https://github.com/occult-kranti/ANDOLAN/actions/runs/38837936134) passed source checks, 51 tests, seven browser cases and production builds, then failed at Pages configuration with `Not Found`; deployment was skipped. The user subsequently enabled Pages, allowing the new workflow to publish. The earlier failures do not describe the current website's availability.

The environment draft adds `api.github.com`, `occult-kranti.github.io`, `uploads.github.com` (release assets) and `results-receiver.actions.githubusercontent.com` (Actions logs) and saves the installation/start instructions. The draft save itself does not confirm activation or a published snapshot: review and save the environment settings, then publish the environment. No additional secret is required for the game itself.
