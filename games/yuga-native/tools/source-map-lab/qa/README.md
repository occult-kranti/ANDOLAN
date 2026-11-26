# Verify the Dust II ground edit

The independent checks read the original compiled map, the finished map, the two rendered scenes and the official navigation mesh. They can run after the import and material tools have exited. The checked-in result records measurements and file identities. The local evidence directory contains the complete per-texture, per-camera and per-navigation-area reports. [Measured result](verification.json)

## Reproduce the evidence

Use Python 3.11 or newer. The audited environment used NumPy 2.3.5, SciPy 1.17.0 and Pillow 12.3.0. The native BSP reader only needs the Python standard library. From this directory, point `LAB` at the local output package.

```sh
LAB=/workspace/ANDOLAN-local/dust2-map-lab
BSP="$LAB/native/original/csgo/maps/de_dust2.bsp"
JADE="$LAB/native/jade/csgo/maps/de_dust2.bsp"
BASE_MODEL="$LAB/models/dust2-baseline.glb"
JADE_MODEL="$LAB/models/dust2-jade.glb"
EVIDENCE="$LAB/evidence"

python3 native.py inventory "$BSP" --output "$EVIDENCE/native-inventory.json"
python3 native.py compare "$BSP" "$JADE" --face-ids "$EVIDENCE/floor-faces.json" --output "$EVIDENCE/native-diff.json"
python3 textures.py "$BSP" "$JADE" "$LAB/content/csgo" "$EVIDENCE/bake.json" --output "$EVIDENCE/texel-diff.json"
python3 scene.py "$BASE_MODEL" "$JADE_MODEL" --bsp "$BSP" --face-ids "$EVIDENCE/floor-faces.json" --output "$EVIDENCE/scene-diff.json"
python3 nav.py "$BASE_MODEL" "$EVIDENCE/official-nav.csv" --bsp "$BSP" --output "$EVIDENCE/nav-support.json"
python3 images.py "$LAB/renders" --output "$EVIDENCE/render-diff.json"
python3 -m unittest discover -s . -p 'test_*.py' -v
```

## What the checks measure

| Question | Independent check |
| --- | --- |
| Which parts of the compiled game changed? | Compare each immutable lump and its descriptor. Permit only a replacement texture-info index on listed faces. Check both light-range face tables, compare every original packed file after decompression and restrict material overrides to original albedo layers. |
| Did the edit preserve surface detail and transparency? | Resolve albedo slots from the original VMTs, decode each original BC-compressed mip including small edge blocks, apply the linear RGB gains, and compare every resulting RGB and alpha value to the packed variant. |
| Did the scene rebuild retain the map? | Count native face IDs, then sample three native positions per face with a 5 mm tolerance. Verify displaced surfaces, brush transforms, placed static model path/skin/transform, and decal source IDs, draw order, materials and face lists. SHA-256 covers the complete GLB binary chunk. A structured comparison of the two scene descriptions permits only selected RGB factors. |
| Which surfaces count as ground? | The edit covers the walkable structural floor. A vertical ray at each original NAV rectangle centre tests visible upward triangles within ±18 Source units. The test reports raised props separately. At remaining centres it traces the original world collision brush planes. The method samples area centres and uses a point hull. |
| Is the edit visible? | Compare the district overview and both objective views at matched cameras. Count pixels changing by at least 12 eight-bit levels in any RGB channel, with a one-pixel inset on the ground mask. Measure spill beyond a two-pixel margin around antialiasing coverage. |

## Interpreting this revision

All 8,840 renderable brush faces and 3,158 static placements registered in the mesh. The original BSP also retains its 1,012 invisible utility faces, collision, entities, lighting and sound references. Blender interprets the recovered materials with its own lighting and shading.

Of 1,118 native NAV centres, 991 had nearby structural ground and every one touched a recolored face. Another 109 landed on separately textured static models, including 56 stair and 16 curb centres. The remaining 18 were within 7.482 Source units of an original invisible collision brush. Raised steps, curbs and crate tops keep their original appearance. Both orange bombsite decals remain on the jade floor.
