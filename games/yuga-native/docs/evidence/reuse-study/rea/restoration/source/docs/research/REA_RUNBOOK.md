# Repeatable local REA research

This toolkit is optional development research; the game does not import it. Existing source checkouts are `/workspace/tooling/rea` and `/workspace/research/sketchbook`; the installed CLI is `/workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs`. No agent configuration or persistent MCP integration was created.

The published npm package was selected from the official repository's package link, pinned to `6.5.0`. Its root SHA-512 integrity is `sha512-C6BG7LyrAdR74mSjertM6PrxJkcNZ2bfQNOJornPo9erDEp2tyPRVYPnV5Yodr+1RqewCQla68WulXlVnveD+A==`. npm enforced lockfile integrity. An independent tarball download through the inherited HTTPS proxy matched the same value. Registry signatures were verified with the public key served at `https://registry.npmjs.org/-/npm/v1/keys`, using SHA-256 ECDSA over `rea-agents@6.5.0:<integrity>`. The exact public inputs and result are saved under `evidence/rea-package-verification*.json`.

The optional whole-install `npm audit signatures` stopped with HTTP 403 while fetching TUF metadata. npm's installed `@sigstore/tuf` identifies `https://tuf-repo-cdn.sigstore.dev` as its default mirror; that host is outside the current managed allowlist. No network policy, integrity expectation or TLS setting was weakened. Root registry verification is narrower than full dependency provenance verification. Retry the standard audit only after the environment permits the required Sigstore service. This does not block source-level game work.

## Restore the CLI in a fresh environment

Use the task's existing isolated checkout, without creating a Git worktree. Check that Node is a supported version and `ps --version` reports procps. Inspect existing paths before copying files; the following restore assumes a fresh `/workspace/tooling/rea-runtime` directory. The saved lockfile pins the observed dependency tree.

```sh
mkdir -p /workspace/tooling/rea-runtime /workspace/tooling/npm-cache
cp docs/research/rea-tool-package.json /workspace/tooling/rea-runtime/package.json
cp docs/research/rea-tool-package-lock.json /workspace/tooling/rea-runtime/package-lock.json
npm --cache /workspace/tooling/npm-cache --prefix /workspace/tooling/rea-runtime ci --ignore-scripts --no-fund
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs --version
```

Lifecycle scripts were not needed for this static lane. Native/terminal providers may need separately reviewed dependencies; this is not a claim that every REA provider works.

Retrieve a pinned reference into a new research directory, keeping it outside the application checkout:

```sh
git clone https://github.com/swift502/Sketchbook.git /workspace/research/sketchbook
git -C /workspace/research/sketchbook checkout --detach 62f4b7986fd1ce1e4f91daba89ef032c20a6ce55
git -C /workspace/research/sketchbook rev-parse HEAD
```

Do not reset or overwrite an existing modified research checkout; verify its revision and cleanliness first. Repository source at the pinned commit and per-file hashes are the reproducibility anchors. REA's whole-directory artifact digest can also reflect the inventoried local artifact; do not assume a changed checkout's digest equals this session's.

## Exact analysis command used

```sh
mkdir -p /workspace/research/rea-output
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  analyze-javascript-application /workspace/research/sketchbook \
  --source-path src/ts/characters/Character.ts \
  --source-path src/ts/characters/VehicleEntryInstance.ts \
  --source-path src/ts/characters/character_states/vehicles/EnteringVehicle.ts \
  --source-path src/ts/characters/character_states/vehicles/Driving.ts \
  --source-path src/ts/characters/character_states/vehicles/ExitingVehicle.ts \
  --source-path src/ts/characters/character_states/vehicles/ExitingStateBase.ts \
  --source-path src/ts/vehicles/VehicleSeat.ts \
  --max-heap-mb 512 --analysis-timeout-ms 30000 --json \
  > /workspace/research/rea-output/sketchbook-application.json
```

This command parses inert source; it does not start Sketchbook, execute its application code or build its old dependencies. REA's default integrity policy remained `fail`. It explicitly excludes 184 inventoried files from semantic analysis.

Produce the focused trace from the retained evidence:

```sh
python - <<'PY'
import json
from pathlib import Path
p = Path('/workspace/research/rea-output')
a = json.loads((p / 'sketchbook-application.json').read_text())
query = {'application': a, 'query': {
    'seed': {'kind': 'property', 'name': 'occupiedBy'},
    'direction': 'backward-provenance'
}}
(p / 'seat-trace-input.json').write_text(json.dumps(query))
PY
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  trace-javascript-semantics /workspace/research/rea-output/seat-trace-input.json \
  --json > /workspace/research/rea-output/seat-trace.json
```

Both commands exited 0. The trace's domain status is `ambiguous`, with `partial` coverage: process success is not a resolved behavior proof. The source evidence ID, graph IDs, selected facts and raw-evidence SHA-256 are in `evidence/rea-sketchbook-summary.json`. The full application evidence is 8,678,205 bytes and remains in the external research directory; the focused 8,002-byte trace is retained in this repository. Saved summary excerpts are derived selections and must not be passed to REA as a full authenticated parent evidence object.

## Why this is the stopping point

The source exposes the local entry/exit boundaries sufficiently for an original implementation contract. More graph inventory would not resolve animation feel, seat races or browser networking: those need ANDOLAN runtime tests. Native binary tooling, GTA game data, JDK/JADX and persistent integrations are not prerequisites for this milestone.
