# Six graphics rounds: shared capture workspace

Root owns the sole heavy lane, CPUs 0,1 with two llvmpipe workers. These tools do
not change runtime code. Baseline originals remain under `docs/evidence/ui-campaign/I3/role03/`.
Use one snapshot for G1–G6; retain each round's source receipt and raw captures.

Before refreshing, stop the owned engine and finish review of the previous take.
Source owners must declare stable files; root completes any required import in
the canonical project. Do **not** import or run the editor in the shared snapshot.
The tool first compares every previous managed file with its seal, including added
or removed files. Any mismatch rejects refresh. Preserve and diagnose that result.

```sh
python3 games/yuga-native/tools/graphics-six/snapshot.py refresh \
  --source /workspace/ANDOLAN/games/yuga-native \
  --project /tmp/yuga-graphics-six-project \
  --store /tmp/yuga-graphics-six-store \
  --round G1 --receipt /tmp/yuga-graphics-six-G1-source.json \
  --harness-overlay tools/visual-rounds/groom_contract.json=/workspace/ANDOLAN/games/yuga-native/tools/graphics-six/hero-camera-contract.json
```

For later rounds use `G2` etc. and a fresh receipt. `--dry-run` makes no writes.
Ordinary source files are independent copies. Compiled imports are copied once
into a content-addressed, read-only store and hardlinked into the snapshot;
canonical imports are never linked. Snapshot and store must share a filesystem.
Previous changed/deleted source bytes are retained by SHA; unchanged files stay
in place. A prior receipt can be reconstructed from current matching files and
the retained `sources/` and `imports/` blobs. Keep the store and all receipts until
root explicitly confirms archival/recovery before cleanup. This is one ~180 MB
source tree plus ~66 MB initial imports, rather than six full freezes.

The raw asset MD5/import-output check detects stale or missing imported inputs.
It does not establish that changed importer settings were regenerated; root owns
that import receipt. Source/cache hashes are checked again after copying. The
snapshot seal covers import-cache mutations that the older render runners omit.
Only explicit JSON capture-contract overlays are permitted. `hero-camera-contract.json`
preserves the corrected r6 eight camera/actor fixtures; it inherits no historical
runtime acceptance claim. Its `groom_contract.json` alias repairs an otherwise
missing input in the canonical old runner.

Verify before and after **each** capture, without overlapping a refresh:

```sh
python3 games/yuga-native/tools/graphics-six/snapshot.py verify \
  --project /tmp/yuga-graphics-six-project
```

Actual native title and ordinary world, four originals, default fresh settings:

```sh
taskset -c 0,1 python3 /tmp/yuga-graphics-six-project/tools/ui-campaign/run.py \
  --mode integrated --project /tmp/yuga-graphics-six-project \
  --plan /tmp/yuga-graphics-six-project/tools/graphics-six/native-plan.json \
  --renderer forward_plus --render-threads 2 --timeout 600 \
  --width 960 --height 600 --display 190 --output /tmp/yuga-g1-native-r1
```

The 960×600 window retains the actual 960×540 framebuffer. Native Tab/Return
opens settings and toggles Moonlit courtyard for the title pair; native N waits
for world `night=true, phase=1, target_phase=1`. The plan returns and exits through
native Quit. It never stages actor positions, rules or outcomes. Keyboard controls
avoid the old integrated runner's missing pointer-layout settlement (package mode
has that protection). Day/night world army clocks continue; these are contextual
views, not identical temporal-state or population comparisons.

Matched hero front/rear/profile/full-body and ordinary camera, eight originals:

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 0,1 python3 /tmp/yuga-graphics-six-project/tools/visual-rounds/run.py \
  --project /tmp/yuga-graphics-six-project --mode groom-stills \
  --context courtyard --display 191 --output /tmp/yuga-g1-hero-r1
```

This preserves the existing 1280×960 framing; shrinking to 960×720 would change
the camera contract. It stages review cameras/positions/lighting and pauses the
world. It observes final modified poses in `modification_processed`, computes
actual imported bounds and stores raw PNGs; it is not native gameplay input or
motion-quality evidence. Front/rear station names describe backgrounds whose
current pixels still need inspection after environment changes.

Both runners accept `--shader-cache-seed /ABSOLUTE/validated/user/cache/mesa`.
Use one known immutable seed, copy it privately, and retain its SHA receipt.
Warm captures do not measure cold startup or hardware FPS. Output paths and X
displays must be unused. Runtime logs, plans, full JSON and PNGs remain primary;
never replace them with a contact sheet or compressed movie alone. A future
continuous take must use the motion owner's exact tape/source and final-pose
observer; neither four UI stills nor the eight hero stills approve continuity.

Verification executed without engines:

```sh
taskset -c 3 python3 games/yuga-native/tests/graphics-six/test_snapshot.py
python3 games/yuga-native/tools/ui-campaign/run.py --dry-run \
  --mode integrated --project /workspace/ANDOLAN/games/yuga-native \
  --plan /workspace/ANDOLAN/games/yuga-native/tools/graphics-six/native-plan.json \
  --renderer forward_plus --render-threads 2 --width 960 --height 600 \
  --display 199 --output /tmp/yuga-g1-dry-only
```

Dry-run validates request parsing, not live label/focus navigation. If a redesigned
label changes, retain the failed plan/run and update the explicit target; never
call product navigation methods to make a native-input claim pass.

The source-pinned sash comparison uses `run_focus.py --case sash-review
--review-branch baseline|candidate` with two separately sealed children. It
captures exactly `rest-front` and `cast-three-quarter`; the common
`sash_uv_capture.gd` checks all three raw hero hashes, motion/finish hashes,
the final 164-bone pose and the complete selected imported sash projection.
The front station is staged; the cast uses the actual public ability at its
declared windup age. Use the same explicit engine and copied Godot/Mesa seeds
for both branches. This helper has a bounded, post-shot audio-mixer cleanup;
it changes no runtime audio behavior or observed pose. Preserve original
failed preflights separately from the successful successor.
