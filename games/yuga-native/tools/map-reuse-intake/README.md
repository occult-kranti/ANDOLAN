# Existing-map element intake

This isolated prototype reuses the existing raw `GLTFDocument` loading path,
one current **CC0 courtyard structural mesh**, its original triangle geometry
and the existing audited **CC0 sandstone PBR adapter/maps**. It creates no new
map geometry and imports no commercial-game code or art.

From repository root:

```sh
python3 games/yuga-native/tools/map-reuse-intake/prepare.py \
  --output /workspace/scratch/map-intake-new
GODOT_SILENCE_ROOT_WARNING=1 OMP_NUM_THREADS=1 godot --headless \
  --path /workspace/scratch/map-intake-new --script res://test_intake.gd
```

The project directory must be fresh and outside the checkout. Preparation
pins the source GLB hash, CC0 metadata and metre/Y-up contract, links that
read-only input, copies the existing PBR adapter exactly and stages only the
small integration harness. It copies **zero map GLB or texture bytes**.
The adapters create in-memory mesh/material/physics resources and scratch
reports; canonical assets and map manifests are unchanged.

`map_loader.gd` accepts only the exact known courtyard hash and one named
`COL_` group: `COL_BEVEL_Warm_carved_sandstone`, 1,296 triangles. It uses Godot's
installed glTF loader, preserves the mesh resource/materials and creates a
static collision shape from the same transformed triangles. Placements allow
rigid rotations/translations; scales, reflections and nonfinite transforms
are rejected. There is no extra conversion of already Y-up metre GLB data.
The embedded-container guard is intentionally narrow and is not a general
validator for arbitrary downloaded models.

The 23 checks exercise actual source import, raw accessor/native coordinate
agreement, collision-face identity and ray hits, the existing three-metre
PBR tile, source immutability, and wrong hash/selector/scale/reflection,
external-resource and truncated-container refusal.

One bounded optional native screenshot can use the existing extracted shared
runtime. Coordinate with the render owner before running it:

```sh
python3 games/yuga-native/tools/map-reuse-intake/capture.py \
  --project /workspace/scratch/map-intake-new \
  --runtime /workspace/scratch/ten-rounds-oct23/runtime/runtime \
  --output /workspace/scratch/map-preview-new --display 188
```

The runner owns and stops only its Xvfb/Godot children. It forces one-thread
Mesa software rendering and captures one 960×640 frame; elapsed time is not
GPU performance. Source selection and a readable screenshot do not accept
the entire map, route design, gameplay authority or a graphics-quality target.

[The source-pinned map reuse packet](../../docs/research/map-code-reuse-oct23/README.md)
contains actual results, license distinctions and the file-level next roadmap.
