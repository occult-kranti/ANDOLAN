# Native visual campaign capture

This captures original Godot Forward+ framebuffers from the playable courtyard. The optional shadow diagnostic can use the actual Confluence world. It does not generate concept art, change product defaults, benchmark a physical GPU, or establish commercial graphics parity.

Read repository `AGENTS.md`, `docs/START_HERE.md` and the native build handbook first. One worker owns the heavy render/import lane. Agree a source freeze before copying; never render a changing shared checkout. Current cloud runs use Godot 4.6.3, the prepared software Vulkan/Xvfb runtime, `taskset -c 2,3` and two llvmpipe threads. Headless source checks can use the other CPUs.

## Freeze and run

Use a new absolute scratch directory. Copy `project.godot`, `assets/`, `scripts/`, `shaders/`, `scenes/`, all `tools/`, and `art/world/` from the agreed native project. Copy its valid `.godot/` import cache only while imports are idle, or run the documented serialized headless import on the scratch copy. Include `.uid` and `.import` metadata. Pin every copied source file with SHA-256 before/after copying and reject a changed source. Save the origin commit, source directory, copy manifest and any deliberately different diagnostic harness in `candidate-origin.json`.

When reconstructing a Git baseline, use `git ls-tree -rz --name-only COMMIT` and read each exact blob; non-NUL output can quote Unicode filenames and silently produce a partial snapshot. A valid cache alone is insufficient: source/import checksum checks must pass. Do not copy credentials, old evidence, or user save files into a snapshot.

Run the tool from the snapshot, with a fresh output and an unused X display:

```bash
taskset -c 2,3 python /workspace/scratch/FROZEN/tools/visual-campaign/run.py \
  --project /workspace/scratch/FROZEN \
  --output /workspace/scratch/NEW-CAPTURE \
  --shader-cache-seed /workspace/scratch/PREVIOUS-CAPTURE-user/cache/mesa \
  --display 158 --title-night
```

The prepared runtime defaults to `/workspace/tooling/native-render/runtime`. `--runtime` and `--godot` can override installed paths. `--dry-run` validates the requested mode and prints the intended command/count without starting processes. The runner creates isolated XDG data/config/cache directories, owns its Xvfb, preserves logs and checks the engine exit status. It refuses reused outputs/displays, incomplete reports, changed source hashes and changed PNG hashes. Never repair an accepted receipt by overwriting its old bytes; use another run.

## Capture modes

| Option | Actual output/scope |
| --- | --- |
| Default | Eight title, near-hero, player-camera, overview and real Piercing Dawn release images |
| `--hero-anchors` | Separate three ordinary views: title day and near hero day/night; no diagnostic overrides |
| `--title-night` | Adds the ninth actual title night view |
| `--ability-reel` | Adds five abilities × windup/release/impact/expiry milestones |
| `--ability ID` | Selects one real ability; repeat for a subset |
| `--ability-night` | Captures selected abilities in both day and night |
| `--abilities-only` | Omits the standard views |
| `--character-detail` | Appends two baseline/optional temple-wisp close-up pairs, last; the candidate remains review-only and was rejected in R2 |
| `--face-ablation` | Separate four-frame run: baseline, sun shadows off only, skin normal maps off only, SSAO off only |
| `--shadow-bias all` | Separate four settings × matched face/gameplay views: baseline .025/.35, depth .1/.35, normal .025/1.0, both .1/1.0 |
| `--shadow-bias confirm` | Baseline .025/.35 and candidate .2/.35, with matched face/gameplay views |
| `--shadow-bias final` | Separate bounded follow-up: defaults .1/2.0, depth2 .2/.35, depth4 .4/.35; two views each |
| `--shadow-bias baseline\|depth\|normal\|both\|defaults\|depth2\|depth4` | One selected shadow setting, two matched views |
| `--shadow-night` | Night lighting for the selected shadow diagnostic |
| `--shadow-world` | Actual Confluence scene/lighting for the selected shadow diagnostic; no courtyard portrait fill |

Ability IDs are `kodanda`, `piercing_dawn`, `measured_step`, `guardian_circle`, `dawn_volley`. Diagnostic runs are separate from ability/standard-view runs. All shadow-bias cases retain dynamic shadows and restore the actual original source settings. The diagnostic baseline explicitly uses historical .025/.35 even after a different default is promoted; it records both the source settings and the historical baseline. Confluence close-up offsets rotate with the actual visual yaw relative to the courtyard PI-radian reset yaw; the ordinary gameplay camera is unchanged. Reported diagnostic values and camera/rig pins identify what was actually captured. An unexecuted mode is capability, not acceptance evidence. The paused Confluence shadow diagnostic disables the world process: location/lighting HUD text can retain its pre-teleport/pre-phase value. Those frames qualify only camera/lighting comparisons, not live HUD synchronization; the separate normal-process film checks per-frame HUD authority.

## Clocks and receipts

The courtyard/diagnostic runner uses a fixed **15 Hz capture/process clock**, normal **60 Hz physics**, and the normal **20 Hz army authority**. It pauses the tree to select review frames. Ability casts enter the real runtime and advance normal authority between milestones; wall/range impacts must not be described as receiver hits. `capture.json` retains complete normalized event payloads, not only phase names. A windup takes one actual physics interval before freezing so short casts are not skipped by a whole capture frame.

`capture.json` pins source bytes before/after, cameras, pose diagnostics, actual PNG hashes, lighting and clocks. `run.json` pins the report, runner and logs. Water animation time is explicitly frozen for consistent composition. Shared framing comparisons establish camera/player/phase/viewport equality, not identical harnesses or identical pixels. LOD selection is recorded as observed. The optional close-ups and shadow pairs additionally pin the complete skeletal pose.

These fixed clocks are **not achieved hardware FPS**. Paused milestones do not prove continuous motion, human-input feel, balance, audio quality or online synchronization.

## Continuous real-receiver film

Use the separate existing `tools/run-rama-gameplay.py` from the same frozen project after visual review:

```bash
taskset -c 2,3 python /workspace/scratch/FROZEN/tools/run-rama-gameplay.py \
  --project /workspace/scratch/FROZEN \
  --output /workspace/scratch/NEW-ACTION-CAPTURE \
  --shader-cache-seed /workspace/scratch/PREVIOUS-CAPTURE-user/cache/mesa \
  --display 159
```

The full run records five actual Confluence ability takes, 363 sequential original frames, 25 original stills and a silent MP4. It validates two actual 60 Hz physics ticks per 30 Hz video frame, accepted casts, live staged receiver receipts, normal expiry, finite animation/effects and per-frame HUD/authority agreement. Low-angle replays and hero hit/defeat/respawn stills are outside the video. Five scene-reset takes are deliberate cuts, not one uninterrupted fight or human OS input. Fixed-rate video is not a GPU benchmark; this film does not exercise adversarial locomotion jitter/braking.

Retain all raw sequence PNGs in the fresh scratch output with their hashes. Archive the compact MP4, 25 original sample PNGs, complete per-frame/event/source/clock manifests, logs and review under `docs/evidence/visual-campaign/capture-action-*`. Mark the full sequence **local-only** unless it is separately published. Do not duplicate hundreds of raw sequence images into Git or delete them while review owns them.

## Preserve and recover exact intermediate sources

Campaign archives are under `docs/evidence/visual-campaign/capture-*`. An `archive.json` maps each retained file to SHA-256 and byte count. `runtime-text-source.json` maps actual `res://` paths to exact frozen runtime text under `source/`. Failed R1 geometry and rejected R2 optional hair evidence remain historical; they must not be rewritten with later fixes.

For recovery, build a **fresh scratch** snapshot from the recorded base commit and matching binary assets, then copy the archived text files to their recorded resource paths. Compare every required binary's SHA-256 with the capture report; final Git assets are usable only when their hashes match. Reconstruct only the listed source set, because additional files in hashed directories also change identity. Missing/mismatched binary inputs remain an explicit recovery gap. Reimport in the serialized lane, verify source/import checksums, and use a new output directory. Never overwrite canonical runtime with an older archive.

Intermediate archives intentionally omit duplicate GLBs and import caches. Historical harnesses are archived alongside runtime text; later added diagnostic flags do not retroactively belong to an earlier run. A replay against different harness/source/engine bytes is a new experiment.
