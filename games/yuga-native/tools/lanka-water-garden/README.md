# Existing-source water-garden candidate

This reviewed module arranges two carved column markers and two low brass diya
assemblies on the existing west reed court's banks. It reuses 29 complete,
position-welded source components from the original CC0 courtyard and its exact
UVs, normals, tangents and materials. Existing water, reeds, lotus and flat ground
are unchanged. It adds no new light, shader, texture source or generated mesh art.

Read [the source, placement and acceptance packet](../../docs/research/reuse-production-continuation/W4/README.md)
before editing or moving it. The canonical game explicitly enables the shared
helper; the isolated fixture opts out before its matched comparison. This is one
small four-feature addition, not a completed district or a full-map art claim.

From the repository root, use fresh outside-checkout outputs:

```sh
python3 games/yuga-native/tools/lanka-water-garden/prepare.py \
  --output /workspace/scratch/water-garden-fresh-selection.json
OMP_NUM_THREADS=1 godot --headless --path games/yuga-native \
  --script tools/lanka-water-garden/bake.gd -- \
  --selection=/workspace/scratch/water-garden-fresh-selection.json \
  --output=/workspace/scratch/water-garden-fresh.scn
OMP_NUM_THREADS=1 godot --headless --path games/yuga-native \
  --script tools/lanka-water-garden/probe.gd -- \
  --output=/workspace/scratch/water-garden-fresh-probe.json
OMP_NUM_THREADS=1 godot --headless --path games/yuga-native \
  --script tools/lanka-water-garden/capture.gd -- --preflight \
  --output=/workspace/scratch/water-garden-fresh-preflight
```

The bake uses the existing native GLTF loader and the prior gate extractor's
whole-triangle array remapping. The retained candidate is a compressed native
scene with bundled textures; scene serialization is not claimed byte reproducible.
`scripts/lanka_water_garden.gd` verifies the exact accepted candidate hash, source provenance, placement,
shared resource counts and collision faces before mounting.

An actual six-view render requires the root's exclusive heavy-render lease:

```sh
python3 games/yuga-native/tools/lanka-water-garden/capture.py \
  --godot /workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot \
  --runtime /workspace/scratch/ten-rounds-oct23/runtime/runtime \
  --output /workspace/scratch/water-garden-fresh-render --display 178 --timeout 240
```

The adapter reuses the established owned-Xvfb runner, two-thread llvmpipe,
qualified Godot 4.6.3, warm caches, MSAA 2× before showing the window and actual
`frame_post_draw` captures. It never invokes editor imports. Headless preflights
and software-render timings do not establish physical-GPU performance.

`tools/lanka-water-garden/mount.gd` is only a wrapper around that canonical helper.
`Garden.build(world)` defaults off; an explicit `Garden.build(world, true)`
requires an identity-transform world and exact source placement. The helper
refuses duplicate mounts. `prepare_army_manifest` deep-copies supplied boxes,
retains prior gate/relay additions, appends four source-bound conservative ground
footprints and rejects moved roots, parents, source clusters/colliders or tampered
metadata. Native triangle physics and the existing planar army remain distinct.
All mesh/material/shape resources are immutable shared inputs; nodes and bodies
are private. Do not modify shared resources through an instance.

The art fixture intentionally holds the real hero/army/kit callbacks and water
clock for matched before/after views. It evaluates the existing Rama idle before
the hold, uses the actual west-facing shoulder-camera transform, preserves all
original bodies and tests real physics. Its staged views are not normal-input
traversal, multiplayer or human playtesting.

The actual default production integration check is:

```sh
OMP_NUM_THREADS=1 godot --headless --path games/yuga-native \
  --script tools/lanka-water-garden/test_integrated.gd -- \
  --output=/workspace/scratch/water-garden-fresh-integrated.json
```

Use `capture.py --integrated-correction` for three current default-world views
with the real UI owner refreshed after staging. The original six matched images
remain separate, with their original source and held-HUD limitation. New renders
still require the root's exclusive heavy-render lease.
