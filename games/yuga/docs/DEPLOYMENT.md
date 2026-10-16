# Deploying YUGA: Confluence

Protocol 2 requires updating the browser bundle and server together. Version-1 servers cannot represent jungle guardians or contested gold.

The browser build can run Practice from a static host. Online matches additionally need a running WebSocket server. The supplied container serves both the built client and the authoritative server on one origin. These files prepare deployment; they do not create a provider account, purchase hosting or establish that a public multiplayer backend is available.

Current candidate: optional hero guides/Practice goals, repaired night lighting, the west coastal gate/shallow Reed Court and renderer-readiness/cast corrections. Some focused guidance/lighting cases have passed, but final regression, packaged build identity, CI, actual video and public smoke remain open in [NEXT_PHASE_PANEL.md](NEXT_PHASE_PANEL.md). The container records below are dated baseline evidence and do not contain all later client changes. No public WSS service has been provisioned.

The current runtime was frozen and pushed at `c39d65a`, with 212 unit tests, full typechecks and lint passing. Those source gates do not substitute for the pending native/CI/build/public checks. The browser ZIP command and first-match instructions are in [README.md](../README.md).

## Files and build context

- [Dockerfile](../Dockerfile): pinned Node 24 base, locked dependency installation, production build, development-dependency pruning and non-root runtime.
- [Dockerfile.dockerignore](../Dockerfile.dockerignore): allowlists the required files from the **repository root** build context. A plain `games/yuga/.dockerignore` would not govern this root-context build, so it is intentionally not used.
- [render.yaml](../render.yaml): prepared single-instance Docker service settings, manual deploys, `/health` check. Its `standard` plan is paid; current pricing/resources have not been verified here. No Render service was created.

Run commands from the repository root, not from `games/yuga`. The lockfile, server TypeScript configuration, Vite configuration and third-party notices live at the root.

## Build and run without Docker

```sh
npm ci
npm run yuga:build
PORT=3005 npm run yuga:start
```

The build writes `dist/yuga/index.html` and `dist/yuga-server/games/yuga/server/index.js`. The server defaults to `0.0.0.0:3005`, serves the client from `dist/yuga`, exposes `GET /health`, and accepts WebSocket upgrades at `/ws`. Start from the repository root because the default static directory is relative to the working directory.

Open `http://localhost:3005/` for the full-stack local build. For a separately hosted browser client, enter that server's URL in **Online team match → Arena server**. The client accepts HTTPS/WSS addresses, and plain HTTP/WS only for loopback development. It normalizes a server root address to `/ws`. Creating a room and joining an existing room must use the same server.

## Container build and local verification

On an ordinary Docker host with working registry access and standard certificate trust:

```sh
docker build -f games/yuga/Dockerfile -t yuga-confluence:local .
docker run --rm --name yuga-arena -p 127.0.0.1:3005:3005 yuga-confluence:local
```

In this managed cloud environment, use the configured Docker daemon, inherited proxy and mounted CA trust. Read the cloud runtime's Docker instructions before changing these commands. The local daemon was checked explicitly; do not replace its context, credentials, storage driver or proxy configuration.

```sh
mkdir -p /tmp/yuga-buildx
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
  -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
  BUILDX_CONFIG=/tmp/yuga-buildx \
  docker --host=unix:///var/run/docker.sock build \
  --secret id=registry_ca,src="$CODEX_PROXY_CERT" \
  -f games/yuga/Dockerfile -t yuga-confluence:local .
```

The writable Buildx metadata directory avoids the managed home directory's read-only filesystem; `DOCKER_CONFIG` and its credentials remain unchanged. The CA is mounted only during networked build steps. It is not copied into an image layer; TLS verification stays enabled. Docker's configured proxy defaults supply build connectivity. Do not unset the network proxy, use host networking to avoid policy, or disable certificate verification. The application currently needs no external HTTPS call to serve a match; a future runtime HTTPS integration would need its own appropriate CA mount/trust setting in this environment.

The container reads `PORT`; its health check uses that same variable. A provider may override it. There is no required writable data directory or persistent volume in this first release. The runtime executes as user `node`.

## Public hosting options

### Publication permission: resolved; release verification pending

The release branch `game/yuga-confluence` has been pushed. Earlier on 16 October 2026, the release coordinator found that the existing GitHub Pages environment, `github-pages`, permitted deployment only from `main`. The integration's request to add the exact new branch policy returned **HTTP 403 — ResourceNotAccessibleByIntegration**. This earlier failure remains historical evidence.

The repository owner subsequently removed the Pages deployment-branch restrictions. The coordinator verified `deployment_branch_policy: null` through the environment API; a branch-policy listing HTTP 404 is expected with no branch policy configured. The earlier branch-policy blocker is resolved through the owner's configuration change. This does not itself publish or validate the expansion: final workflow deployment and public client verification remain pending in this record. No public WSS backend is claimed. The protocol-2 container record below verifies the expansion locally; the earlier fourteen-hero record is retained separately as history.

### One full-stack service

Deploy the container on a provider that supports persistent WebSocket connections. Terminate TLS at its reverse proxy and route both HTTP and WebSocket upgrades to the container's `PORT`. Preserve `/ws`; use an idle timeout that permits the server's heartbeat. Test the actual public HTTPS and WSS routes from separate browser contexts.

The nested Render YAML is a configuration template for this branch. If the provider's Blueprint workflow does not select nested configuration files, create the Docker service using its explicit fields: repository root context, `games/yuga/Dockerfile`, branch `game/yuga-confluence`, one instance and `/health`. Do not replace the existing root ANDOLAN Render configuration. No provider credentials or automated provider API integration were available in this task.

One instance is required by the current in-memory room model. Independent replicas do not share room codes, identity tokens or match state. Horizontal scaling needs explicit room routing/shared ownership and new tests; setting a replica count above one is not sufficient.

### Static client plus a separate WSS service

The main release workflow may publish `dist/yuga` under `/ANDOLAN/yuga/`. That provides Practice. Pages does not execute the Node server. Players can enter the separately deployed secure arena URL, or use the game's invite URL containing that server and room code. Do not place credentials or reconnect tokens into invitation URLs.

The browser currently does not guess a production server from an arbitrary static host. A blank Arena server field on a public static deployment is expected until an operator supplies a real endpoint. Publishing static files is not a public multiplayer launch.

## Match lifetime and operational limits

Rooms, simulation state and hashed reconnect-token identities are in process memory. A process restart, deploy or crash loses those matches and invalidates their reconnect tokens. There is no match checkpoint, account database or cross-process reconnect persistence. A disk mount does not change this behavior.

The current source bounds the process to 96 transports and 32 rooms, with six human seats per match and bots filling open places. These are admission limits, not verified safe production concurrency. It rejects oversized messages, bounds per-socket traffic, and expires abandoned rooms/reservations. See the systems/QA evidence for actual measured machine, actor counts and timing. Health status is liveness/current counts, not proof of available performance headroom.

At this preparation point, `PORT` is the deployment environment control; the server's default host is `0.0.0.0`. Additional origin/capacity settings must be documented only if implemented and tested. Current room tokens authorize reconnect to a specific room; they are not accounts, ranked identities or an anti-cheat system.

Before broad public multiplayer availability, establish a hosting owner and budget, TLS/WebSocket routing, origin/rate policy, capacity monitoring, deployment rollback and an honest restart message. Keep match admission within measured limits. Stop/restart only the YUGA service under review; the existing ANDOLAN service has separate data and lifecycle.

## Protocol-2 jungle container verification

This record precedes the optional-guidance and city-lighting client changes described in [NEXT_PHASE_PANEL.md](NEXT_PHASE_PANEL.md). A new production build and delivery check must identify those later inputs; this image does not contain them.

On 16 October 2026 at 18:42 UTC, the frozen jungle/minion expansion built successfully and passed its bounded production-container smoke. [jungle-deployment-container.json](evidence/jungle-deployment-container.json) records image `sha256:884c5f30ef74d9679f347e7794a010517cbd323cbb5cb0e12ed277a9f284515b`, the actual HTTP asset URLs, both model manifests and all hashes. The 54 relevant working-tree build inputs had aggregate SHA-256 `f677e5b659cb324ed9f8e94c3e9f8ac4cf8ce6db002c952a9a6466b3d708e123` before the build and after the smoke; the image carried the same fingerprint label. These file hashes identify the frozen inputs even where the recorded Git HEAD predates uncommitted work.

The container served a 6,443,593-byte client with SHA-256 `d4e5ea8107408a0a42be439e6ee0c8b3497123ed2987a1444acaf1987df547a2`. All **fourteen hero and seven unit GLBs**, 50,998,516 bytes total, were fetched through the URLs declared by that built client and matched the exact manifest bytes and SHA-256 values. The client contained no development-only window hook; `/health`, welcomes and snapshots reported protocol 2, including four neutral slots and gold-shard state.

Two independent real Node WebSocket transports joined one room, moved through ordinary server input messages and observed each other's authoritative state. A spawn upgrade charged exactly 100 credits; a same-process reconnect preserved its single actor identity and purchase, and repeating the command ID did not charge twice. Restarting only the owned test container discarded the in-memory room/token as documented, returned the expected recoverable error and then accepted a fresh protocol-2 match.

The runtime used Node 24.22.0 as UID 1000 (`node`), with TypeScript and the temporary build CA absent. Build TLS verification stayed enabled. The full dependency installation reported three high-severity advisories across 171 audited packages; the subsequent production prune reported zero vulnerabilities across seven audited packages. This records those two npm results separately and does not declare the development graph or future advisories clear. No automatic dependency upgrade was applied during the frozen verification.

The **2.868-second smoke** is HTTP/hash and real-socket evidence, not a browser render, full combat match, public WSS service or performance-capacity test. The build ran after the isolated systems stress window and before QA's long native soak. Its owned, loopback-only test container was removed after verification; all three pre-existing ANDOLAN containers retained their IDs and running state. No public multiplayer backend was provisioned. The later [native soak](evidence/jungle-native-soak-check.json) independently passed the normal 480-second Practice finish and fresh replay under the stated software-render budget. Its ready-to-finish wall time was 518.823 seconds, so it does not establish exact real-time throughput or consumer-hardware performance. The [built production browser check](evidence/jungle-production-check.json) separately passed at root and nested mounts with all 21 models. Public publication remains a distinct gate. The historical record below remains separate.

## Historical fourteen-hero verification record

The protocol-1 baseline predates the seven-unit, jungle and contested-gold expansion. It does not validate the new protocol-2 build. On 16 October 2026, that frozen runtime/art Docker build and bounded local production-container smoke passed. [deployment-container.json](evidence/deployment-container.json) records the exact image, client/model hashes, configuration hashes and scope. Image `sha256:1e5ee12d523b02f390eaa4a239763240c37484f3cea17ba6844556fa47aed454` served a 6,414,473-byte client with SHA-256 `46193afd937a3ca572351de148833b27cc1a71a9bc52d3ad1117d6ffaf924a26`. All fourteen external GLBs—46,520,992 bytes total—were fetched through the actual URLs declared by the production HTML and matched the frozen asset manifest. The production HTML contained no development-only window hook.

This check caught and fixed a real packaging regression: relative model URLs generated for `assets/*.js` resolved from `index.html` after the script was inlined, returning 404. The build now generates GLB URLs with `new URL(filename, document.baseURI)`, retaining the `assets/` prefix for root and nested static hosting. The failed-image HTTP evidence remains in [deployment-container-url-regression.json](evidence/deployment-container-url-regression.json); the earlier pre-asset container result remains in [deployment-container-initial.json](evidence/deployment-container-initial.json). Neither earlier image was the accepted fourteen-hero baseline container.

Two independent real Node WebSocket transports joined one room with distinct identities and observed an authoritative input acknowledgment. Reconnect preserved one actor identity. Restart of that owned container discarded the in-memory room, and the old room/token received the expected recoverable error. The runtime ran as UID 1000, with the build CA absent and TypeScript removed. The production pruning step reported zero audited vulnerabilities; this is not a claim about every development dependency or future advisories. The owned test container was stopped/removed; existing ANDOLAN containers were untouched.

The 1.232-second socket/HTTP/model-hash smoke did not launch a browser, exercise a complete combat match, establish public WSS connectivity or measure capacity. No public backend was deployed. Browser interaction, two-client combat, public deployment and capacity tests remain distinct QA records; a container pass cannot substitute for them.

Before claiming public multiplayer, record the deployed source/image identity and verify:

1. Public HTTPS client and `/health` return the expected release without development hooks.
2. Two independent browsers create/join one room through real public WSS and agree on authoritative state.
3. Reconnect preserves one identity during the same process lifetime; a stale token after restart gives a recoverable error.
4. Shutdown/redeploy behavior and provider limits are documented; ordinary user errors do not leave an endless loading state.
5. The existing `/ANDOLAN/` game still works and retains separate settings/session keys.

The longer service, art, balance and operations obligations remain in [PRODUCTION_ROADMAP.md](PRODUCTION_ROADMAP.md).
