# YUGA production observatory

A read-only dashboard for an explicitly recorded production run. It combines job records with current local CPU/memory/NVIDIA telemetry and the checkout's Git identity. The UI lives in `web/`; no third-party Python packages are required. Use Python 3.10+ and Git. The normal development server binds **127.0.0.1 only**; it supplies no command-execution, download, authentication, model-control or cleanup API.

The [build-farm guide](../../docs/GAME_BUILD_FARM.md), [job runner](../local-swarm/CONTROL.md) and [six project skills](../../../../.agents/skills/README.md) own those separate workflows. This tool observes work; it does not create an autonomous swarm or make a GPU available.

## Start a recorded run

From the repository root:

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py init \
  --workspace /absolute/path/to/ANDOLAN \
  --run-id production-001 --title 'YUGA — hero and world production'
python3 games/yuga-native/tools/build-observatory/observatory.py serve \
  --workspace /absolute/path/to/ANDOLAN --port 8765
```

`init` refuses to replace an existing run. Every command accepts `--state-dir /absolute/private/run-directory` for an independent run. By default, mutable state and its interprocess lock are under the checkout's ignored `.local-swarm/observatory/`. It stores local process identities privately; do not publish that raw state. Only the public API/export projection removes those identities. Never put secrets, credential URLs, private hostnames or sensitive narrative text in any record; arbitrary producer text is not automatically redacted.

The server polls neither remote model services nor GPU providers. Its local memory values use the lower applicable Linux cgroup limit and `/proc/meminfo` values. CPU quota is distinct from logical CPU count. The NVIDIA probe is a bounded local `nvidia-smi` query containing only name, total/used memory and utilization; an absent executable means **NVIDIA telemetry unavailable**, not proof that all possible graphics backends are absent. Unsupported platform measurements remain null. It does not read process command lines or environment variables.

The HTTP routes are:

- `GET /api/status`: sampled source/host telemetry and projected job/context records.
- `GET /api/health`: service availability and `read_only: true`; not a game-quality or model-quality check.
- `GET /`: static UI and approved file types under `web/`, including root-reviewed `web/media/` artifacts.

Host headers are restricted to the bound loopback host/port. The service sends no wildcard CORS header. Static files reject traversal, encoded traversal and symlink components; private directories are not exposed. Requests, threads, file sizes and JSON payloads have explicit bounds. Use the supported platform's normal private tunnel or serve a static export when sharing; this script intentionally offers no public-bind switch.

## Record real work

Save an explicit JSON job record outside the tracked source, then submit it:

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py emit \
  --workspace /absolute/path/to/ANDOLAN --record /absolute/private/artist-job.json
```

A queued job:

```json
{
  "kind": "job",
  "id": "rama-material-pass",
  "title": "Rama material and silhouette review",
  "owner": "W3 hero artist",
  "stage": "Hero intake",
  "status": "queued",
  "device": "CPU",
  "model": null,
  "summary": "Reuse the existing Rama mesh and rig; inspect the actual four views before editing.",
  "outputs": [],
  "next_step": "Record the chosen source hashes and launch the bounded Blender job."
}
```

The same ID updates that job atomically. Unspecified fields remain from its earlier record. Status values are `queued`, `running`, `review`, `complete`, `blocked`, `failed` and `stale`. Model and device are producer declarations, not automatic model detection. A label such as `public GPU` describes that recorded service job; it does not turn the local host's GPU availability on.

A `running` update must include exactly one liveness method:

- `"pid": 12345`: an existing Linux process owned by the invoking OS user. The tool records boot identity and process start ticks, then checks them on every sample. An ended, zombie, reused or inaccessible process becomes **stale**, never automatically complete. PID tracking does not inspect its command or prove a particular program ran. Non-Linux process identity is currently unsupported; use an explicit heartbeat there.
- `"heartbeat_ttl_seconds": 120`: a producer-reported heartbeat, valid for 5–300 seconds after receipt. Submit another explicit heartbeat while that remote/hosted job is actually active. The public record identifies this as heartbeat verification. It proves a recent producer report, not remote GPU utilization or generated-output correctness.

An ordinary progress update without either field preserves the earlier liveness deadline; it does not silently refresh a heartbeat. Clock anomalies and expired heartbeats project as stale. Raw producer status is retained privately for inspection.

Completion is explicit and requires a nonempty summary plus at least one evidence output, for example:

```json
{
  "id": "rama-material-pass",
  "status": "review",
  "summary": "Four actual source renders are ready for independent artist review; runtime acceptance remains open.",
  "outputs": [
    {"label": "Front render", "kind": "image", "url": "media/rama-front.png"},
    {"label": "Source report", "kind": "report", "path": "games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md"}
  ],
  "next_step": "Compare garment contact and silhouette across all views."
}
```

Use `complete` only for the named job's verified scope. A job completion does not accept a whole game milestone. Output `path` is a safe repository-relative display path; the server does not read arbitrary repository files from it. Output `url` is either `media/...`, the exact `viewer/` or `viewer/index.html` route, or HTTPS without user credentials. Producers must retain the actual evidence separately and have another owner assess it.

## Add stages, assets and reuse sources

`configure --record /absolute/private/context.json` accepts any subset of three arrays. Supplied arrays replace their corresponding context list; omitted lists are preserved. It cannot alter jobs or liveness.

```json
{
  "milestones": [
    {"id": "hero-intake", "title": "Hero and rig intake", "status": "review", "evidence": "Matched source renders; continuous motion still open."}
  ],
  "assets": [
    {"id": "diya", "title": "Lotus diya", "status": "source candidate", "image_url": "media/diya-front.png", "model_url": "media/diya.glb", "summary": "Generated source mesh; collision, scale, LOD and flame authoring remain open."}
  ],
  "sources": [
    {"name": "Blender", "url": "https://www.blender.org/", "license": "GPL tool; outputs have separate provenance", "status": "existing toolchain"}
  ]
}
```

## Publish an honest saved snapshot

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py export \
  --workspace /absolute/path/to/ANDOLAN \
  --output games/yuga-native/tools/build-observatory/web/status.json
```

Export performs one real local sample, writes `mode: "snapshot"` and retains its `collected_at`. Reopening that static JSON never updates its timestamp. The UI polls `/api/status` while the local server is available; otherwise it loads `status.json` and labels the view **saved snapshot**, with its age. Static hosting provides a readable progress report, not a live server or background agent execution. A published snapshot updates only when the producer deliberately exports and republishes it.

Export strips private PID/birth tracking fields. Inspect the public JSON and copy only reviewed artifacts into `web/media/` before publication. No raw receipts, model weights, environment files, credentials or machine-specific absolute paths belong there. Local model/source caches remain outside Git.

## Verification

```sh
python3 -m unittest discover \
  -s games/yuga-native/tools/build-observatory -p 'test_*.py' -v
```

The suite exercises real localhost HTTP, an owned child process and exit/reuse identity, heartbeat expiry, snapshot timestamps, eight simultaneous CLI updates, malformed/oversized data, source/GPU telemetry edge cases, read-only routes, Host rejection, static traversal and file/directory symlink escapes. GPU telemetry is mocked; no GPU inference, laptop execution, PS4 connection or complete native-game run is implied.

The Windows byte-lock code is present but unexecuted here. Run the suite on the intended OS before claiming that platform; Linux/WSL is the measured baseline. Standard-library HTTP is suitable for this bounded local development tool, not an Internet production service.

## Inspect the generated Rama mesh

The [source-model viewer](viewer-source/README.md) reuses existing PlayCanvas 2.23.3 and the repository's painted PBR environment helper. Its locally bundled `/viewer/` route displays the actual generated GLB from `web/media/rama-generated.glb`, with pointer/keyboard orbit and zoom/reset. The UI explicitly labels it unrigged with no animations. Build commands, MIT/font notices, actual browser checks and source-quality limits are documented with that viewer. The static export/publisher must copy the compiled `web/viewer/` and approved model/media; it must not copy `viewer-source/` or Node dependencies.
