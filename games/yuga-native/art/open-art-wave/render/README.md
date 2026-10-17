# Native material comparison fixture

This renderer captures four matched pairs in the actual native scenes: courtyard
780 px camera target/near mesh at day and night, then Confluence 350 px camera
target/mid mesh at day and night. A fixed three-quarter front camera exposes
front cloth and the mantle side. The projected rest bounds are recorded; the
target number is not an exact screen-space silhouette measurement.

The optional role07 fixture changes only supported cloth uniforms on existing
secondary-owned materials. The rig, per-bone pose, face/morphs, mesh/skin IDs,
material identity/shader, nonowned uniforms, secondary offset, controller clocks,
camera and light/exposure remain frozen. Full before/candidate/restored states
are recorded; unbind must restore every full baseline material state exactly.
Raw engine frame counters remain observations and are excluded from functional
equality because the renderer advances them even while gameplay is paused.

Eight original PNGs are saved without image editing. Crops may be made only as
separately labelled diagnostic copies; they never replace raw evidence. Shader
water time is frozen through its existing animation_speed input; any unsupported
TIME shader is reported. Temporal renderer history can still differ. The
comparison does not test continuous deformation, gameplay input, commercial art
quality, KHR sheen equivalence or achieved real-time hardware performance.

R1's full replacement profile remains archived with its exact original source.
Its brighter blue color and lost gold albedo motif were rejected for default
promotion. The finite R2 correction adds `--preserve-albedo`: the fixture keeps
the original `base_color`, `base_texture` and `use_base_texture`, while adopting
only the candidate's roughness/normal-related profile. Those three original
albedo inputs remain inside the functional equality hash. The report records
the literal profile ID `preserve-original-albedo_cc0-roughness-normal-v1` and
the twelve permitted uniforms. Without the option, the full fifteen-uniform
profile is explicit and separate.

**Request root's heavy render slot first.** Root must serialize native imports,
freeze runtime and fixture sources, and provide a warmed optional Mesa cache.
The real project's `art/.gdignore` is deliberately preserved. A normal editor
import exits successfully without importing these candidate textures. Use an
isolated scratch project containing byte copies of project.godot, assets,
scripts, shaders, scenes, the world manifest and this candidate subtree (without
an ancestor .gdignore); copy the warm .godot cache optionally. Include the
open-cloth test and its .uid for the separate actual resource check. Do not use
symlinks to mutable source or remove the real art ignore file.

First import that fixture; then enable mipmaps on only its three candidate
texture `.import` configurations and reimport those textures. This review-only
import metadata is not promoted into the real project. The renderer records
source/import hashes and settings. Original and copied source bytes are compared
before and after the take in `source-identity.json`; only the three fixture-only
texture `.import` sidecars may lack an original counterpart.
Candidate maps must have generated and actual imported mip chains. The harness
checks source/destination MD5 import freshness plus SHA-256 source/import pins.
It never edits runtime sources, mesh assets or import configurations.

```sh
python3 games/yuga-native/art/open-art-wave/render/run.py --output /workspace/scratch/open-art-material-r1 --dry-run
# After explicit slot grant and native import:
taskset -c 2,3 python3 games/yuga-native/art/open-art-wave/render/run.py --project /workspace/scratch/open-art-material-fixture-r2 --output /workspace/scratch/open-art-material-r2 --display 147 --shader-cache-seed /path/to/owned/warm/mesa --preserve-albedo
```

The runner owns its Xvfb child, fresh XDG/user/cache directories and bounded
Godot subprocess. It cleans up its display on success or failure and preserves
new failure outputs. `capture-run.json` validates the actual report schema,
four expected scenes/LOD/lighting pairs, imported mipmaps, images and exact
restoration. Warnings are retained explicitly. Source/report/PNG byte pins and
text source snapshots support independent review; process exit alone is not
accepted as capture completion.
