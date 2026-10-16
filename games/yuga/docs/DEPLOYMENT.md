# Deploying YUGA: Confluence

The browser build can run Practice from a static host. Online matches additionally need a running WebSocket server. The supplied container serves both the built client and the authoritative server on one origin. These files prepare deployment; they do not create a provider account, purchase hosting or establish that a public multiplayer backend is available.

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

## Release verification record

On 16 October 2026, the Docker build and bounded local production-container smoke passed. [deployment-container.json](evidence/deployment-container.json) records the exact image, client hash, configuration hashes and scope. Image `sha256:dc35c1929b0a9234abf0ca185afc4b5f0a72b7a286cb4dc2a53a93f20b618818` served a 6,371,640-byte client with SHA-256 `2390695788ee665fce1f8136e4bb5497a5eb943bc5bf2364a60fd6ae5e51ff20`. The test used an intermediate working-tree build while later client/renderer/simulation fixes were still underway; rebuild the release image after the final source freeze.

Two independent real Node WebSocket transports joined one room with distinct identities and observed an authoritative input acknowledgment. Reconnect preserved one actor identity. Restart of that owned container discarded the in-memory room, and the old room/token received the expected recoverable error. The runtime ran as UID 1000, with the build CA absent and TypeScript removed. The production pruning step reported zero audited vulnerabilities; this is not a claim about every development dependency or future advisories. The owned test container was stopped/removed; existing ANDOLAN containers were untouched.

The 1.27-second socket/HTTP smoke did not launch a browser, exercise a complete combat match, establish public WSS connectivity or measure capacity. No public backend was deployed. Browser interaction, two-client combat, public deployment and capacity tests remain distinct QA gates.

Before claiming public multiplayer, record the deployed source/image identity and verify:

1. Public HTTPS client and `/health` return the expected release without development hooks.
2. Two independent browsers create/join one room through real public WSS and agree on authoritative state.
3. Reconnect preserves one identity during the same process lifetime; a stale token after restart gives a recoverable error.
4. Shutdown/redeploy behavior and provider limits are documented; ordinary user errors do not leave an endless loading state.
5. The existing `/ANDOLAN/` game still works and retains separate settings/session keys.

The longer service, art, balance and operations obligations remain in [PRODUCTION_ROADMAP.md](PRODUCTION_ROADMAP.md).
