# YUGA production observatory and reuse-first art stages

The [observatory source](../tools/build-observatory/README.md) is a read-only progress dashboard for actual jobs, model/tool identities, outputs and next steps. The [reuse stage](research/production-reuse-oct23/README.md) owns source decisions and the next five dependent production gates. The [art packet](../art/production-stage-oct23/README.md) distinguishes the existing animated Rama from the new, unrigged GPU-generated source. Neither a concept image nor a clean dashboard closes the commercial graphics target.

The [latest ten-stage checkpoint](research/ten-rounds-oct23/README.md) continues
those sources with six specialists. It records accepted compatibility/world
work, actual effects motion and rejected hero cleanup/binding candidates.
Its [next-owner queue](research/ten-rounds-oct23/NEXT_SIX_TASKS.md) names the
remaining artistic and gameplay gates. Current cloud observations use
`.local-swarm/observatory-ten-rounds/` on loopback port **8767**; pass that
`--state-dir` explicitly when resuming this run. The default port/state below
describe the earlier run. Private state is ignored by Git and must be
initialized afresh if absent; never restore another process's liveness.

The [next ten gated stages](research/ten-rounds-oct23/REUSE_FIRST_NEXT_TEN.md)
assign six owners around existing production sources. Separate dashboard jobs
track the [Rama-family template](research/hero-family-reuse-oct23/README.md),
[CC0 map intake](research/map-code-reuse-oct23/README.md) and protected donor-hair
study. Shared resources, isolated previews and rejected masks do not count as
new finished heroes or a finished map. There is no active local inference
server or attached production GPU in this checkpoint; hosted agents and
bounded CPU authoring/render jobs are recorded separately.

## View the work

The [public dashboard](https://occult-kranti.github.io/ANDOLAN/production/) and [interactive source viewer](https://occult-kranti.github.io/ANDOLAN/production/viewer/) were first deployed from source `069ab775`. Latest checkpoint publication is recorded in [the new publication packet](research/ten-rounds-oct23/publication/README.md). [The independent public-byte audit](research/production-stage-oct23/publication/README.md) verifies 19 successful HTTP observations, 13 exact source-file matches and five preserved game/lab entry points. GitHub Pages serves a **saved snapshot**. Its collection timestamp and recorded-running labels remain visible; polling that file does not make the cloud's hardware live. The browser renders the actual self-hosted GLB using the project's existing PlayCanvas engine, with orbit/zoom/reset controls. It does not turn the source mesh into an animated game hero.

The live worker view runs while its ordinary local service is running:

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py serve \
  --workspace /absolute/path/to/ANDOLAN --port 8765
```

The current cloud run has local state under `.local-swarm/observatory/`, ignored by Git. A new machine needs its own `init` and explicit job records; private process IDs are not copied from another host. On your laptop, open the local service in your browser after starting it. This cloud's loopback service has no public forwarding route. The public snapshot is the accessible handoff when the cloud service is unavailable.

## What the dashboard means

- **Live worker observation:** a fresh API response from the running local observer. CPU quota, available memory and NVIDIA telemetry describe that machine only.
- **Running job:** a matching owned process-birth identity, or an explicit owner heartbeat that expires within five minutes. A process exit or expired heartbeat becomes **stale** until an explicit outcome is recorded. Hosted-agent heartbeats are owner reports, not measured GPU utilization.
- **Complete job:** a named bounded deliverable, summary and retained output. It is not completion of its larger roadmap stage, the hero, or the game.
- **Public GPU job:** the supported service's recorded submission and result. It never changes the cloud host into a CUDA machine. Provider wall time is separate from GPU kernel timing.
- **Saved snapshot / paused / stale:** historical data whose age is shown. There is no assumed background agent activity after a chat ends.

The HTTP surface has no execution, download, delete, credential or job-control endpoint. Local CLI commands record state; the separate [job runner](../tools/local-swarm/CONTROL.md) handles selected commands with the invoking user's privileges. It is not an OS sandbox. Keep real client/account/container isolation and supported login paths.

## Reuse already implemented

| Component | Reused input and actual result | Remaining acceptance |
| --- | --- | --- |
| Engine and rendering | Existing Godot 4.6.3, Blender 4.3.2/Cycles and PlayCanvas 2.23.3; existing browser lighting/GLB loading code | Physical-GPU performance, player feel and complete game integration remain separate |
| Existing character | Exact existing Rama GLB, 164-bone rig and embedded idle; actual locked views in a retained Blender composition | Existing contact, face and hair limits remain open; this pass did not replace the character |
| Original new character source | New image based on the existing original Rama/Hanuman/Sita direction, then one supported anonymous TRELLIS.2 generation and export | Initial 512 mesh has softened face/relief and severe rear hair defects; no skin or animation. One 1024 comparison was provider-quota denied; no 1024 output exists |
| World/material | Existing courtyard, water, diya and a verified 6.22 MB Poly Haven CC0 sandstone set | Look development is narrower than the playable Vayu-court collision/route gate |
| Optimization | Existing glTF-Transform/meshoptimizer adapter exercised on the prior diya | It refused unsupported `EXT_texture_webp`; no optimized derivative was produced |
| Source lessons | Existing REA/Ghidra, open-engine and game-system studies retained | Commercial clients/replays were not supplied; no new native-binary replication is claimed |

The [GPU report](research/production-stage-oct23/gpu/README.md) retains official API/source metadata, request identities, failures/successes, previews and hashes. Supported public quota is an available compute path. A CTF label does not supply access to someone else's account, keys, quota or machine; no such bypass was used.

## Stage plan and six owners

1. **Source and material intake:** freeze original art, licenses, model input, code/tool versions and source hashes. Do not download another bulk library where the current kit is adequate.
2. **Character source comparison:** compare actual front and rear geometry at the same camera/light settings. Keep the generated source outside runtime. Choose an artist-controlled cleanup plan from observed defects.
3. **Topology and rig:** repair hair, face, hands, ornament/cape reconstruction and material seams; then author topology/LODs, scale, skinning and deformation checks. A one-material triangulated mesh is not ready merely because it loads.
4. **World and action pilot:** finish one existing Vayu landing court with truthful collision/routes, and one continuous authored hero action with root/feet/hand/bow contact. Preserve the current authority and accepted descent behavior.
5. **Integration and delivery:** qualify the exact playable candidate, full journeys and actual network authority before expanding roster/team size. Preserve FG06 native 3v3 before six-hero/6v6 expansion. Android stays deferred.

Assign W1 independent acceptance, W2 UI/input, W3 hero art/rigging, W4 world/materials/collision, W5 motion/combat and W6 models/build/delivery. Each owner returns its exact files, input/output hashes, executed checks, actual images or footage, defects and next gate. Use the existing [next-six-owner queue](evidence/desktop-finish/continuation-oct18b/NEXT_SIX_OWNERS.md), not a new claim of completed rounds.

The current stage delivered a monitoring tool, source/model intake and bounded render evidence. Full Deadlock-level art/motion quality remains open. The desktop ledger remains **17/78 accepted packets and 0/13 complete rounds**; Android remains **0/108 implementation packets**, deferred.

## Publication and maintenance

The dedicated workflow rebuilds the existing browser site from its exact previously deployed source before adding `/production/`; it does not replace the site root with the dashboard. The publisher verifies pre-existing sibling file hashes remain unchanged during the additive copy, validates snapshot mode and copies only approved web/media/viewer/license files. Rebuilding that pinned source does not establish byte equality with an older deployment; public checks have their own receipt.

After an observable job result, emit its CLI record and export `web/status.json`. Then publish a reviewed snapshot. Never keep an abandoned process or anonymous demo marked running indefinitely, and never run a heartbeat loop that outlives its actual owner just to make the dashboard appear busy.
