# C5 original connected hair sculpt

Rejected inactive editable coarse hair source for native YUGA. Both C5
four-view actuals completed. Root and the source owner reject the final major
forms; see [the final actual review](ACTUAL_REVIEW.md). The canonical hero and C1–C4 remain
unchanged. No runtime GLB promotion or art acceptance is implied.

The first [shape contract](SHAPE_CONTRACT.md) replaces C4's separate scalp
panels, peg and padded tail lofts with one connected closed editable cage.
Only C4's thin seated scalp support is reused. Shared edges join scalp, an
oblique gather patch and a rear/nape extension. The master keeps live Subdivision
1; there is no voxel union. The [first actual review](ACTUAL_REVIEW_R1.md) found
a smooth helmet, narrow capped gather and a thin C-shaped rear sheet.

Root authorized one [combined major-shape correction](CORRECTION_CONTRACT.md).
It moves the rear front plane inward toward occiput/nape, sculpts broad oblique
folds into the body's depth, and gives its three lower reaches unequal taper.
The gather ramp broadens under the untouched tie and returns into a fuller
asymmetric folded bun. Broad scalp flow planes are sculpted directly into outer
vertices. No fine strand/groove pass is included. The initial 20 mm bun-height
limit was superseded by root's actual-image finding; numeric dimensions do not
own the visual gate.

| Take | Editable scene SHA256 | Cage |
| --- | --- | --- |
| First | `08822fc61ceaf28079f5b1e35f363c9dba74e8bb93a372c08cf6943fc3ff1d5c` | 9,427 vertices / 9,584 faces |
| Single correction | `beb880db906dc429520215eafd8f3106d408cc8de28dde84f1e2cda08b5a4f57` | 9,551 vertices / 9,708 faces |

Exact editable scenes, original prepared cages, source/derived mesh data,
semantic snapshots, projection/check reports and logs are retained under
[authoring-payload](authoring-payload/). The recovery map pins every retained
path and its scratch hardlink. No payload bytes were physically duplicated.
Original executed helpers are `author_cage_r1.py` and `build_cage_r1.py`; current
un-suffixed helpers create the one correction. The fixed parent is the final
C4 scene, SHA256
`da97ad89b5660eadc688eb58e4c73cad42b7b3f767daefb99c17028758439a88`.

Both pure-Python cage preparations, Blender source saves and fresh reloads
exited 0. Each cage has one connected component, zero boundary/nonmanifold edges
and no unused vertices. Fresh reloads preserve protected head/crown/tie,
references/rig geometry, cameras, materials, lights, world and scene settings.
Process-only `session_uid` and derived `users` counts are excluded. All four
camera-fit gates pass. Blender emits its known unsupported denoiser enum warning
during property census; it did not prevent save or checks. These are source-owner
checks, not independent fit or art approval.

Executed correction source command from `/workspace/ANDOLAN` (fresh output only):

```sh
taskset -c 3 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 blender --background games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r4/authoring-payload/build-r2/whole-hair-volume-r4.blend --threads 1 --python-exit-code 1 --python games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r5/build_cage.py -- --cage /workspace/scratch/yuga-continuation-W3-r1/preparation-r2/source-cage.json.gz --output /workspace/scratch/yuga-continuation-W3-r1/build-r2
```

`capture_volume.py` is unchanged from C4, SHA256
`0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7`.
W1 owns the actual four 1024×1024 authoring views and their preservation. It uses
32 raw CPU Cycles samples and disables unsupported denoising only in memory,
without saving either scene. See [the exact handoff](CAPTURE_HANDOFF.md).
The cast-angle view is an authoring view, not an animated game cast.

Source work ran only after W1 admitted CPU3 and storage exceeded 500 MiB. No
download, installation, runtime export/import, canonical model edit, animation,
rig transfer, GLB or promotion occurred. Buried scalp seating is permitted;
actual visible skin and crown/tie appearance own the bounded fit decision.
All eight originals were opened by the source owner. Root independently opened
the four final originals and rejected them. The correction budget is exhausted;
no further C5 geometry, raster or promotion will run.
