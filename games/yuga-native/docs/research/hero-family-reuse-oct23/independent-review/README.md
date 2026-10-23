# Independent Rama-family authoring review — 23 October 2026

**Decision: accepted for the tested authoring-template scope after one correction pass.**
This accepts reuse of the existing Rama resources and the isolated Arjuna-labelled
authoring setup. Arjuna still looks like Rama. It does not accept a finished new
hero, new anatomy, production art, gameplay, roster promotion or hardware quality.

Task: independent hero-family intake QA, supporting FG02-T03/T04 and future roster
authoring. Product: native YUGA. Baseline branch `game/yuga-native-production`,
HEAD `8501c28dca3fae43d9fb89ed153d04943fe193eb`. The implementation owner is
`rounds_hero_rig`; the independent reviewer owns only this directory and
`/workspace/scratch/hero-family-independent-oct23`. No product, Git, workflow,
roadmap or shared-source edits were made by this review.

The disproof condition was an incompatible actual candidate receiving `ok:true`,
a donor/source pin changing without rejection, duplicate live skeletons, broken
shared-source references, or a template claiming finished-hero status.

## Frozen inputs

| Input | SHA-256 |
| --- | --- |
| Corrected `tools/hero-family-reuse/intake.py` | `d7c0741e4bf3d84f973618eddc201abbdb78928bd36835e607c2da85dfdeb579` |
| Corrected `rama-family-manifest.json` | `33b3b93522849761204fd9b68c57e0a311f487969089dce61bd4b9c3077116b1` |
| `tools/hero-family-reuse/family_template.gd` | `c09fb7f8d3347f885b91b50364e7a6de194a88a7c57cdd35c4ccaa3524962a8a` |
| Canonical `assets/heroes/rama-hero.glb`, 36,049,948 bytes | `db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e` |
| Saved rig-only Blender scaffold, 1,047,787 bytes | `8e277ace274e577470edb0dc7d7b020ce11d32849ed45d2f5da837ad74be700b` |

The final manifest has 19 direct source/resource pins: three GLBs, the runtime
animation library, hero codex, eight runtime scripts, the secondary shader and
five finish maps. All actual hashes match. Each individual pin also rejects a
zero-hash mutation: [all-pin-drift.json](all-pin-drift.json). The detailed final
source and evidence index is [receipt.json](receipt.json).

## What was proven

| Scoped claim | Actual evidence and result |
| --- | --- |
| Canonical rig/skin contract | One GLB skin, 164 ordered bones, exact parents/rest/binds, three named skinned mesh nodes, valid bounded weights, semantic masks and required face shapes. Actual modified candidate files exercise rejection; the canonical positive remains accepted. |
| Animation distinction | The runtime `.tres` has 23 clips. The GLB has nine embedded actions: cast, cast1, cast2, cast3, defeat, fire, idle, jump and run. The Blender scaffold retains nine actions with hashes matching the original save/reopen report. It references the 23 runtime clips externally; they were not converted into 23 Blender actions. |
| LOD and ownership | Final headless setup reports one live 164-bone rig and three levels. Four body/bow LOD mesh instances and two remapped skins are owned by each actor; the near face remains the unique face owner. This does not assert zero allocation. |
| Actual shared resources | Two separately configured templates share all three canonical near mesh resources and the external AnimationLibrary while retaining independent skeleton state. Each instance has exactly one skeleton. |
| Socket and motion wrapper | Five finite sockets; the new wrapper rejects an unknown socket. Actual run/draw/hold/release/recovery completes and duplicate release is rejected. This is a bounded functional motion check. |
| Saved authoring scaffold | Independent Blender 4.3.2 reopen finds one 164-bone rig, nine matching actions and no mesh/image datablocks. Its properties preserve the canonical geometry hash/path, external runtime library and authoring-only flags. Geometry is referenced by metadata for reimport; this is not a live Blender geometry link. |
| Failure lifecycle | A rejected Hanuman-labelled template has no motion helper and cannot retry setup in the same failed instance. Configured instances remain templates with gameplay/finished/runtime promotion flags false. |

Final executed results:

- [counterexamples-r2.json](counterexamples-r2.json): **24/24**, with stable intake
  and manifest hashes and no uncaught exceptions.
- [owner-tests-final.txt](owner-tests-final.txt): **20/20** regression tests,
  exit 0, 28.082 seconds, independently run after the correction.
- [runtime-final.json](runtime-final.json): **13/13** Godot 4.6.3 headless checks,
  exit 0 and empty stderr.
- [resource-sharing-final.json](resource-sharing-final.json): **10/10** independent
  resource-sharing/lifecycle checks, exit 0 and empty stderr.
- [blender-reopen.json](blender-reopen.json): **6/6** independent saved-file checks,
  exit 0; rig signature and all nine action hashes match the owner's report.
- [cli-final.json](cli-final.json): unskinned and non-finite mesh candidates each
  return structured rejection and CLI exit 2, with empty stderr.

## Findings and the single correction pass

The original 17 tests passed but actual GLBs exposed eight false accepts: remove
the body skin binding; remove a primitive's JOINTS or WEIGHTS; use an out-of-range
joint index; translate the body 50 m; change a surface to another existing
material; add an unreviewed skinned mesh; or give the body a non-finite transform.
See [counterexamples-r1.json](counterexamples-r1.json), the frozen original
[intake](intake-r1-frozen.py) and [manifest](manifest-r1-frozen.json).

During that same correction pass, an actual JOINTS accessor with
`normalized:true` still passed. Its witness and intermediate source hash are
retained in [normalized-joints-r2-in-progress.json](normalized-joints-r2-in-progress.json).
The original manifest also omitted the directly used shader and five finish
maps. The correction adds mesh skin/attribute/index/type checks, finite mesh
positions/transforms, mesh count/name/transform checks, per-surface material
roles, structured malformed-source rejection and all six missing pins.

The final replay rejects all of these exact retained witnesses. Bone order,
parents, rest, inverse binds, material names, unsupported motion, unknown socket,
declared extra anatomy, non-bow weapons, false finished-hero claims, wrong source
hashes and source-pin drift are also rejected. The detailed error codes and
fixture SHA-256 values are in the JSON reports. Full GLB witnesses remain in the
exclusive scratch directory; only reports, reproducible scripts and the small
frozen original implementation/manifest are stored here.

## Exact executed commands

Run from `/workspace/ANDOLAN`. Output paths below identify the retained originals;
choose fresh output names for another run.

```bash
python3 -m unittest discover -s games/yuga-native/tools/hero-family-reuse -p test_intake.py -v

python3 games/yuga-native/docs/research/hero-family-reuse-oct23/independent-review/run_counterexamples.py \
  --project games/yuga-native \
  --output /workspace/scratch/hero-family-independent-oct23/r1

PYTHONDONTWRITEBYTECODE=1 python3 games/yuga-native/docs/research/hero-family-reuse-oct23/independent-review/recheck_counterexamples.py \
  --project games/yuga-native \
  --scratch /workspace/scratch/hero-family-independent-oct23 \
  --output /workspace/scratch/hero-family-independent-oct23/counterexamples-r2.json

timeout 45s blender --background \
  games/yuga-native/docs/research/hero-family-reuse-oct23/pilot/arjuna-rig-authoring-template.blend \
  --threads 2 \
  --python games/yuga-native/docs/research/hero-family-reuse-oct23/independent-review/probe_blender_reopen.py \
  -- /workspace/scratch/hero-family-independent-oct23/blender-reopen.json
```

Both Godot probes were run with this exact two-CPU wrapper, once for each
`--script`/`--output` pair recorded below:

```bash
timeout 45s python3 - <<'PY'
import os
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
os.environ['OMP_NUM_THREADS']='2'
os.execvp('godot', ['godot', '--headless', '--path', 'games/yuga-native',
    '--script', 'tools/hero-family-reuse/probe_template.gd', '--',
    '--output=/workspace/scratch/hero-family-independent-oct23/runtime-final.json'])
PY
```

The second pair is
`docs/research/hero-family-reuse-oct23/independent-review/probe_resource_sharing.gd`
and `/workspace/scratch/hero-family-independent-oct23/resource-sharing-final.json`.
The CLI fixture commands and exact captured results are in `cli-final.json`.
The first generator was run against the original intake; rerunning it against
the corrected intake should reproduce the rejection results instead.

No raster capture, physical GPU, human art review, input/game-feel review,
networked match, hardware performance or publication was run. Unique faces,
silhouettes, outfits, bows, choreography, contacts, appendages, abilities and
production review remain with their respective authoring owners. The next owner
is the lead for integration of this bounded authoring tool; a new hero-art owner
must supply original art and motion before any roster acceptance.
