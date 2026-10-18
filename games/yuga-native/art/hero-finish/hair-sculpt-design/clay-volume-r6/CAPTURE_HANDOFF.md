# C6 fixed-view clay capture

Source preparation and fresh reload pass; actual visual acceptance is pending. W1 owns the serialized actual raster lane. No source changes are permitted while the admitted take runs.

- Scene: `/workspace/scratch/yuga-next-W3-r1/build-r1/whole-hair-sculpt-r6.blend`
- Exact scene SHA256: `e41417ff09dd5d22de35b0f3b0b7dd5db3711057fe11ffe1f6b3fd819f044aee`
- Scene bytes: 2,342,250. Editable copy is preserved by hardlink under this packet's `authoring-payload/`.
- Capture helper: `games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r6/capture_sculpt.py`
- Helper SHA256: `0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7`
- Four exact cameras: `VIEW_front`, `VIEW_anatomical-left-profile`, `VIEW_rear`, `VIEW_cast-angle-authoring`. Their transforms/lenses and the protected head/crown/tie, other meshes, materials, lights/world and saved scene context are unchanged from C5.
- Fresh-load check SHA256: `4b157220bcbd675621daf262e3e7a9aabbe71ab239ee1616bfafde5170dd3366`.
- Projection SHA256: `49081b993887ed507f9222661d81bbbb519998f5b9fffed0537db8e04cee4cc3`.
- Source census: 594 vertices, 592 faces, one connected component, zero boundary/nonmanifold edges; unapplied subdivision2. These facts do not accept the silhouette, visible contact, rig or runtime.

After W1's explicit capture slot and a fresh ≥500 MiB disk check, run the installed Blender 4.3.2 with CPU affinity0,1, `LP_NUM_THREADS=2`, `--threads 2`, raw32samples and no denoiser. Use W1's existing private process environment rather than copying assets or caches:

```sh
taskset -c 0,1 blender --background /workspace/scratch/yuga-next-W3-r1/build-r1/whole-hair-sculpt-r6.blend \
  --threads 2 \
  --python /workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r6/capture_sculpt.py \
  -- --expected-scene-sha256 e41417ff09dd5d22de35b0f3b0b7dd5db3711057fe11ffe1f6b3fd819f044aee \
  --output /workspace/scratch/yuga-next-W3-r1/actual-r1
```

Review all four original PNGs directly. Compare low oblique fold versus peg/puck; directional scalp flow versus helmet/panels; rounded asymmetric overlapping falls versus sheets or inflated paired straps; long terminal taper and staggered silhouette; visible scalp breakthrough and readable fixed hardware. Hidden inner seating intersections are allowed. The fourth view is rest-space cast-angle authoring, not the animated public game cast. No UV, rig, LOD, GLB, animation or canonical promotion is implied by this capture.

The initial coarse rectangular-fold corner fit is retained separately; a bounded pre-save edit seats those corners inside the circular tie. Its isolated subdivision2 preflight is a fit fact, not a full evaluated triangle-contact or visual conclusion. Read `SHAPE_CONTRACT.md` and the adjacent continuation `W3-art-r1/source-receipt.json` for scope and exact finite source files. Existing C1–C5 source/originals remain unchanged.
