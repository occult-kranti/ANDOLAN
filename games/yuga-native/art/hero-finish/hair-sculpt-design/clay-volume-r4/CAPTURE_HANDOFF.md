# C4 exact actual capture handoff

Final single-correction r2 source-owner checks passed. Both actual takes completed; final art was rejected. This is the executed recipe, not a request for another capture. W1 owns raster CPU0/1.
The capture never saved the scene. Each operation required at least 500 MiB free.

```sh
taskset -c 0,1 env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 blender --background /workspace/scratch/yuga-hair-volume-r4/build-r2/whole-hair-volume-r4.blend --threads 2 --python-exit-code 1 --python /workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r4/capture_volume.py -- --output /workspace/scratch/yuga-hair-volume-r4/actual-r2 --expected-scene-sha256 da97ad89b5660eadc688eb58e4c73cad42b7b3f767daefb99c17028758439a88
```

Capture helper SHA256:
`0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7`.
Inspect all originals directly: front, anatomical-left-profile, rear and
cast-angle-authoring. This last is an authoring camera, not an animated game cast.

Judge intended continuous scalp coverage, shallow directional sweeps, no giant
separate temple paddles, filled compact fold, tapered volumetric overlapping
falls, and readable crown rail/tie. Buried inner scalp seating may intersect.
Do not infer visual acceptance from topology or projection checks. C3 remains
sealed and inactive. The one allowed correction has been used. This is the final C4 actual gate; no fine strands or runtime promotion.

Executed r1: scene `a4428ee52ed703cfe344329b4fbf097b06833efcb8eb93b0aacc518cbd7cbc1a`, output `actual-r1`, clean exit 0 in 90.940 seconds.
Executed r2: exact command above, clean exit 0 in 94.301 seconds.
All eight originals were opened by source owner, W1 and root. Final review is `ACTUAL_REVIEW.md`. No more raster or geometry correction in this packet.
