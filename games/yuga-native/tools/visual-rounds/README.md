# Bounded visual round controls

Read `tools/visual-campaign/README.md` first. This extension reuses its real-world,
light, rig, framebuffer and renderer controls. One worker owns all heavy Godot,
Blender and render jobs. Root reassigned the heavy lane to CPUs 0,1 on
18 October 2026, with two llvmpipe threads; lightweight work uses CPUs 2,3.
Earlier R2/R3 jobs used CPUs 2,3 and retain those original execution receipts.

Freeze exact runtime Git blobs into a fresh scratch project:

```sh
python3 games/yuga-native/tools/visual-rounds/freeze.py \
  --repo /workspace/ANDOLAN --commit COMMIT \
  --output /workspace/scratch/visual-round2/capture-NEW-project \
  --harness /workspace/ANDOLAN/games/yuga-native/tools/visual-rounds
```

The freezer uses NUL-delimited Git paths, omits node_modules, verifies copied
cache stability and checks source MD5s against 170 import receipts. A candidate
overlay must have its own manifest and import receipt; regenerate changed imports
in its isolated project before rendering. Never copy credentials or user saves.

```sh
taskset -c 0,1 python3 /workspace/scratch/visual-round2/capture-NEW-project/tools/visual-rounds/run.py \
  --project /workspace/scratch/visual-round2/capture-NEW-project \
  --output /workspace/scratch/visual-round2/capture-NEW-court \
  --context courtyard --display 160 \
  --shader-cache-seed /absolute/validated-run-user/cache/mesa
```

All output directories, logs and displays must be fresh. `--dry-run` validates the
request without rendering. Static modes use current runtime lights and shadows;
the existing title portrait fill is off. Face views use a fixed head-bone target,
32 degree FOV and fixed metric offsets, independent of changed mesh bounds.
Action stills use the actual paused posed-head origin, the same metric offset,
and 42 degree FOV. Their CPU projection gate includes the actual imported face,
lips, and central head/neck skin with a 24-pixel border. Run
`check_action_framing.gd` headlessly before a new action capture; this cheap gate
does not replace inspection of the raw originals for occlusion and art quality.
Original full 1280 by 960 framebuffers remain untouched.

| Mode / context | Raw PNGs | Scope |
| --- | ---: | --- |
| `stills`, `courtyard` | 10 | Front, both three-quarter views, profile, ordinary gameplay; day/night |
| `stills`, `stone` | 2 | Confluence face against existing honey sandstone; day/night |
| `stills`, `foliage` | 2 | Historical station ID: Confluence coast/mixed architecture; day/night |
| `forms`, `courtyard` | 3 | Front, left three-quarter and profile in daylight; geometry-only isolation |
| `probe`, `courtyard` | 1 | Matched daylight three-quarter control for one-variable material diagnostics |
| `continuity`, `courtyard` | 36 | Adjacent actual frames: blink, Kodanda, Piercing cancellation |
| `actions`, `courtyard` | 5 | One actual late-windup face/neck pose for each current ability |
| `groom-stills`, `courtyard` | 8 | Corrected gallery front/rear/profile, light/dark full body, dark rear night and ordinary gameplay |
| `groom-continuity`, `courtyard` | 150 | Five seconds of adjacent actual movement, stops, Kodanda, Measured Step and reset |
| `groom-probe`, `courtyard` | 1 | Dark rear control for a declared isolated diagnostic |
| `groom-diagnostic`, `courtyard` | 3 | Rear/profile rest and source-bound Measured Step recoil shoulder witness |
| `groom-actions`, `courtyard` | 6 | Five actual action phases plus matched reduced-effects Dawn Volley |

The continuity take stages 181 public facial-owner updates at 60 Hz while the
world is paused, recording that setup explicitly; it does not write morph values
or claim naturally elapsed gameplay. The 36 captured frames then run normal
runtime updates at fixed 30 Hz. The take must include actual blink closure and
reopening, a real release and real cancellation. Silent MP4 encoding is only a
review convenience; PNG hashes and full JSON remain primary evidence. Capture
rate is simulation sampling, never measured consumer-GPU performance.

Every shot pins camera, viewport, light/exposure/shadow policy, player transform,
visual yaw, LOD, rig pose and facial state. The runner requires unchanged source,
raw hashes, native success and clean engine logs. Reviewers must inspect the
pixels; passing receipt checks do not establish art quality or full gameplay.

Context stations came from R2-02 scene geometry/ray queries. Courtyard gameplay
does not establish Confluence gameplay visibility. The optional indigo/brass
station and broader moving-camera/cascade tests remain separate until executed.
The planned foliage ray hit a tree behind the actor, but actual framebuffers show
mostly coast and architecture around the silhouette. Those originals remain a
matched second Confluence context; they do not close the dark-foliage contrast
gate. Name each source or lighting overlay explicitly in the evidence index.

R3 uses `capture_groom.gd` with a frozen `groom_contract.json`. The corrected
contract is `docs/evidence/visual-rounds/round3/role12/capture-contract-r6.json`:
the gallery deck is at y=.44 m, and its staged actor origin is at y=.4401 m.
The role02 station at y=.05 m is superseded. Each actual shot records a downward
collision-world ground ray; source scene geometry alone is insufficient.

Before rendering, run the same script with `--preflight` under the headless
engine at `--fixed-fps 60`. This advances normal runtime updates and verifies
the eight still bounds or twelve sampled continuous poses. It produces
`preflight.json`, never a framebuffer receipt. During the rendered take every
frame projects the actual imported visible vertices, live morphs, inverse binds,
and actual secondary shader offsets. Final bone globals are observed inside
`SkeletonModifier3D.modification_processed`, before Godot restores public poses.
The 24-pixel framing gate does not prove unobstructed visibility or hair/cloth
collision clearance; inspect the full original frames.

The R3 continuous camera follows actor translation in `frame_pre_draw` so its
stored transform matches the rendered camera. Controls use real InputMap actions,
runtime casts and scene reset. There is no manual secondary animation or pose
writer. The comparator checks final rendered pose pins, secondary state, velocity,
ground contact, render settings and existing camera/light/face/LOD controls.
Authored masked/anchored vertex counts remain in each receipt but are excluded
from secondary dynamics equality when the intended candidate changes hair
geometry. Limits, offsets, velocities, elapsed/reset state and ownership reports
still must match.

`groom-diagnostic` reproduces the archived source test through a real public
Measured Step cast and controlled army/player stepping, then checks all 164
completed bone matrices against `groom_recoil_reference.json`. It assigns no
stored bone transforms. Label this paused staged witness explicitly; it is not
normal-speed gameplay. `groom-actions` instead advances normal runtime updates
until the actual authority age reaches the requested phase. Its separately pinned
`groom_action_contract.json` requires native Target03 aiming, actual floor contact,
release/stage checks, and visible receiver/warning instance bounds. Neither mode
substitutes projection checks for inspection of the original images.
