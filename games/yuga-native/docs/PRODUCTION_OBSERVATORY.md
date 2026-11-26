# YUGA production observatory and reuse-first art stages

## Ember Rite map and hero balance

The current handoff follows four two-site maps and the playable Hanuman and Rama skirmish changes through three panel rounds. Select a map in the Observatory to compare the site entry leads, dry rotation and remaining quench time, then rehearse the route or print the floorplans. The figures come from the route graph. Human pick rates, round outcomes and performance on players’ hardware still need playtests. [Public dashboard](https://occult-kranti.github.io/ANDOLAN/production/#atlas) · [Route drill](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/rehearsal.html) · [Printable atlas](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/yuga-map-atlas.pdf)

The selector reads the same generated timing file on GitHub Pages and on a local worker. The publisher copies that file, the standalone drill, the PDF, the massing overview and the four individual SVG architecture sheets from their canonical atlas locations. The dashboard receipt binds their byte lengths and SHA‑256 digests to the publication commit. The queue links the architectural sources, balance decisions and next playtests. The separate Rust download contains the skirmish. [Atlas and floorplans](design/ember-rite-5v5/atlas/README.md) · [Balance model](design/ember-rite-5v5/atlas/BALANCE_MATH.md) · [Research](design/ember-rite-5v5/atlas/RESEARCH_ROUNDS.md) · [Hero decisions](design/ember-rite-5v5/HERO_BALANCE.md) · [Panel roadmap](design/ember-rite-5v5/atlas/PANEL_ROADMAP.md) · [Game download](../../yuga-rust/downloads/yuga-rust-confluence.zip?raw=true)

On a fresh clone, run these commands from the repository root. The first command seeds a new local record directory with the outcomes in the checked-in snapshot. A worker you already initialized needs only the second command. Open `http://127.0.0.1:8769/` to view local observations. CPU, memory and optional NVIDIA readings now come from that host.

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py resume \
  --workspace "$PWD" --state-dir "$PWD/.local-swarm/observatory-ember-rite" \
  --snapshot games/yuga-native/tools/build-observatory/web/status.json
python3 games/yuga-native/tools/build-observatory/observatory.py serve \
  --workspace "$PWD" --state-dir "$PWD/.local-swarm/observatory-ember-rite" --port 8769
```

The preceding public Sanctum checkpoint retains its own dated run, visual previews, eight job records and receipts. Its media remains addressable in the Observatory. [Previous public data](https://github.com/occult-kranti/ANDOLAN/blob/82b1a4d310f1ea1068f23d068102b61a033b110f/games/yuga-native/tools/build-observatory/web/status.json) · [Sanctum publication evidence](https://github.com/occult-kranti/ANDOLAN/tree/82b1a4d310f1ea1068f23d068102b61a033b110f/games/yuga-native/tools/build-observatory/evidence/sanctum-publication-r1)

The published Pages path reads its adjacent snapshot directly. A worker at the loopback root samples its live API. Custom hosts can supply the live API or fall back to their own snapshot. Bookmark the blocked-work view to follow outstanding defects across reloads. [Blocked work](https://occult-kranti.github.io/ANDOLAN/production/#blocked)

## Earlier art runs

The [reuse into playable integration run](research/reuse-production-continuation/README.md) used ignored state `.local-swarm/observatory-reuse-production-continuation` on loopback port **8768**. Its jobs separate integrated banks/camera, the typed authority factory, diagnostics and rejected hair appearances.

The [observatory source](../tools/build-observatory/README.md) is a read-only progress dashboard for actual jobs, model/tool identities, outputs and next steps. The [reuse stage](research/production-reuse-oct23/README.md) owns source decisions and the next five dependent production gates. The [art packet](../art/production-stage-oct23/README.md) distinguishes the existing animated Rama from the new, unrigged GPU-generated source. Neither a concept image nor a clean dashboard closes the commercial graphics target.

The [October ten-stage checkpoint](research/ten-rounds-oct23/README.md) continues
those sources with six specialists. It records accepted compatibility/world
work, actual effects motion and rejected hero cleanup/binding candidates.
Its [next-owner queue](research/ten-rounds-oct23/NEXT_SIX_TASKS.md) names the
remaining artistic and gameplay gates. Its cloud observations used
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

The public dashboard and interactive source viewer were first deployed from source `069ab775`. An October audit recorded 19 successful HTTP observations, 13 exact source-file matches and five preserved game/lab entry points. GitHub Pages serves a saved snapshot with its original collection timestamp. The viewer renders a self-hosted GLB using PlayCanvas, with orbit, zoom and reset controls. [Source viewer](https://occult-kranti.github.io/ANDOLAN/production/viewer/) · [October publication packet](research/ten-rounds-oct23/publication/README.md) · [Initial public-byte audit](research/production-stage-oct23/publication/README.md)

The live worker view runs while its ordinary local service is running:

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py serve \
  --workspace /absolute/path/to/ANDOLAN --port 8765
```

The original cloud run used local state under `.local-swarm/observatory/`, ignored by Git. A new machine can start an empty record via `init` or seed saved outcomes via `resume`. Process identity and hardware readings belong to the local worker. The public snapshot provides the handoff between workers.

## What the dashboard means

- **Live worker observation:** a fresh API response from the running local observer. CPU quota, available memory and NVIDIA telemetry describe that machine only.
- **Running job:** a matching owned process-birth identity, or an explicit owner heartbeat that expires within five minutes. A process exit or expired heartbeat becomes **stale** until an explicit outcome is recorded. Hosted-agent heartbeats are owner reports, not measured GPU utilization.
- **Complete job:** a named bounded deliverable, summary and retained output. It is not completion of its larger roadmap stage, the hero, or the game.
- **Public GPU job:** the supported service's recorded submission and result. It never changes the cloud host into a CUDA machine. Provider wall time is separate from GPU kernel timing.
- **Saved snapshot / paused / stale:** historical data whose age is shown. There is no assumed background agent activity after a chat ends.

The HTTP surface has no execution, download, delete, credential or job-control endpoint. Local CLI commands record state; the separate [job runner](../tools/local-swarm/CONTROL.md) handles selected commands with the invoking user's privileges. It is not an OS sandbox. Keep real client/account/container isolation and supported login paths.

## October art reuse

| Component | Reused input and actual result | Remaining acceptance |
| --- | --- | --- |
| Engine and rendering | Existing Godot 4.6.3, Blender 4.3.2/Cycles and PlayCanvas 2.23.3; existing browser lighting/GLB loading code | Physical-GPU performance, player feel and complete game integration remain separate |
| Existing character | Exact existing Rama GLB, 164-bone rig and embedded idle; actual locked views in a retained Blender composition | Existing contact, face and hair limits remain open; this pass did not replace the character |
| Original new character source | New image based on the existing original Rama/Hanuman/Sita direction, then one supported anonymous TRELLIS.2 generation and export | Initial 512 mesh has softened face/relief and severe rear hair defects; no skin or animation. One 1024 comparison was provider-quota denied; no 1024 output exists |
| World/material | Existing courtyard, water, diya and a verified 6.22 MB Poly Haven CC0 sandstone set | Look development is narrower than the playable Vayu-court collision/route gate |
| Optimization | Existing glTF-Transform/meshoptimizer adapter exercised on the prior diya | It refused unsupported `EXT_texture_webp`; no optimized derivative was produced |
| Source lessons | Existing REA/Ghidra, open-engine and game-system studies retained | Commercial clients/replays were not supplied; no new native-binary replication is claimed |

The [GPU report](research/production-stage-oct23/gpu/README.md) retains official API/source metadata, request identities, failures/successes, previews and hashes. Supported public quota is an available compute path. A CTF label does not supply access to someone else's account, keys, quota or machine; no such bypass was used.

## October art stage plan and six owners

1. **Source and material intake:** freeze original art, licenses, model input, code/tool versions and source hashes. Do not download another bulk library where the current kit is adequate.
2. **Character source comparison:** compare actual front and rear geometry at the same camera/light settings. Keep the generated source outside runtime. Choose an artist-controlled cleanup plan from observed defects.
3. **Topology and rig:** repair hair, face, hands, ornament/cape reconstruction and material seams; then author topology/LODs, scale, skinning and deformation checks. A one-material triangulated mesh is not ready merely because it loads.
4. **World and action pilot:** finish one existing Vayu landing court with truthful collision/routes, and one continuous authored hero action with root/feet/hand/bow contact. Preserve the current authority and accepted descent behavior.
5. **Integration and delivery:** qualify the exact playable candidate, full journeys and actual network authority before expanding roster/team size. Preserve FG06 native 3v3 before six-hero/6v6 expansion. Android stays deferred.

Assign W1 independent acceptance, W2 UI/input, W3 hero art/rigging, W4 world/materials/collision, W5 motion/combat and W6 models/build/delivery. Each owner returns its exact files, input/output hashes, executed checks, actual images or footage, defects and next gate. Use the existing [next-six-owner queue](evidence/desktop-finish/continuation-oct18b/NEXT_SIX_OWNERS.md), not a new claim of completed rounds.

That October checkpoint delivered the observer, source intake and bounded render evidence. Its desktop ledger recorded 17 of 78 accepted packets and zero of 13 complete rounds. The Android ledger recorded zero of 108 implementation packets.

## Publication and maintenance

On `game/yuga-hanuman-trial`, a push touching an Ember Rite design file, the current Rust ZIP or the dashboard runs the dedicated Pages workflow. It rebuilds the preserved game and lab baseline at `176b6f8e71fcffd3d570d96e66643d8cb9893603`, checks every pre-existing file digest, and publishes the dashboard under `/production/`. The publication receipt gives the actual deployed source and the file census. [Additive Pages workflow](../../../.github/workflows/yuga-observatory.yml) · [Public receipt](https://occult-kranti.github.io/ANDOLAN/production/publication.json)

After an observable job result, emit its CLI record and export `web/status.json`. Then publish a reviewed snapshot. Never keep an abandoned process or anonymous demo marked running indefinitely, and never run a heartbeat loop that outlives its actual owner just to make the dashboard appear busy.
