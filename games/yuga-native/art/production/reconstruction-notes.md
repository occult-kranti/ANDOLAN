# Rama: reconstructed editable source and surface correction

FG02-T01 bounded art packet, 17 October 2026. The original `rama-authored.blend` is still unavailable. `reconstruction-rama.blend` is a new editable reconstruction imported from the committed licensed GLB. It does not recover the original modeling history, separate authored costume pieces, modifiers or original Blender action implementation.

## What changed

The runtime correction moves electric cobalt toward a quieter indigo, yellow ivory toward warm linen, bright gold toward rougher brass, and skin toward a less saturated warm palette. Eye, iris, lip and leather values provide clearer material separation. Low-amplitude original woven fields replace ten embedded albedo/roughness images. Mild vertex tints describe broad garment folds and cheek/temple variation; they do not displace geometry or simulate cloth. Five existing normal images remain embedded, with reduced strength.

The original 59,759 vertices, 100,938 triangles, ten material slots, 164 joints and nine clips remain. Every original byte in the 6,500,208-byte BIN prefix is retained. Node transforms/names, skins, inverse binds, original accessors, geometry, UVs, normals, skin weights and animation samples are unchanged. Runtime generation appends ten new image payloads and three vertex-colour accessors; it does not re-export the armature through Blender. This deliberately retains some superseded image bytes, trading a modest file-size increase for an inspectable preservation guarantee. The GLB grows from 7,541,640 to 7,901,132 bytes; no triangle or draw-surface increase is introduced.

The motion/grip worker owns the separate optional carry modifier. Its compatible-target record must preserve the old motion target pin and reference the exact structural evidence for this material-only target. The surface pass itself does not curl fingers, move the bow, change sockets, fix posture or modify gameplay.

## Source, ownership and provenance

- `reconstruction-source.glb` is the pinned pre-correction input, SHA256 `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`.
- `reconstruction-source-provenance.json` preserves its original attribution and historical assertions. MakeHuman anatomy is CC0; the project costume, hair, bow and procedural animation are original. No commercial-game model was imported.
- New deterministic material fields and vertex tints are original CC0-1.0 work. `reconstruction-manifest.json` pins the generator, input/output and embedded image bytes.
- `reconstruction-rama.blend` packs fifteen images, one armature and nine imported actions. The second mesh is Blender's imported bone-display helper, not an additional runtime character surface. `reconstruction-editable.json` pins this actual file and its evaluated samples.
- `rama-production.provenance.json` and the identical package copy `NOTICE/RAMA-PRODUCTION-PROVENANCE.json` identify the reconstructed source and explicitly distinguish historical predecessor fields from fresh checks.

The first scratch reconstruction incorrectly called `Image.pack()` again on already packed GLB images with empty external paths, leaving a saved file without usable textures. It was rejected. The corrected importer preserves packed data, rejects missing images, and its reopened file passed fifteen-image/164-bone/nine-action checks. The failed scratch artifact and report remain under `/workspace/scratch/yuga-hero-reconstruction-r1`; they are not the editable source shipped here.

## Rejected surface pass and colour correction

Actual motion-capture stills from the first surface pass showed skin becoming pale beige and cobalt becoming pastel. Pixel inspection identified a palette-space authoring error: the source PNG used directly encoded palette values, while the first generator applied an extra linear-to-sRGB transfer. This was not evidence of a Godot double-gamma defect. Source → rejected centre pixels were skin (139,73,38) → (173,141,120), cobalt (9,40,132) → (66,95,146), and ivory (219,197,147) → (222,217,201).

Revision2 uses explicitly encoded sRGB albedo palettes without another transfer; roughness stays linear data and simple glTF colour factors keep their specified linear semantics. Current centre pixels are skin (151,98,68), indigo (18,42,91), linen (212,202,166). Current tests check these ranges. Running those tests against the retained pale candidate correctly fails the reproducibility and palette gates. `reconstruction.surface-r1.generator.py`, `.manifest.json`, `.validation.json` and `.diagnosis.md` retain the exact rejected generator and evidence; its GLB and editable file remain under the pinned scratch rejection directory. Earlier motion captures keep their original surface hash and only support rig-equivalent behavioral conclusions; they are not relabelled as current-surface art.

## Rebuild and verify

Run from the repository root, in an isolated scratch directory. Coordinate runtime replacement, imports and renders with the integration owner.

```sh
python3 games/yuga-native/art/production/reconstruct_rama.py --output /workspace/scratch/rama-next/rama-production.glb --manifest /workspace/scratch/rama-next/staged.json
/usr/bin/blender -b -t 1 --python games/yuga-native/art/production/reconstruct_rama.py -- --editable-from /workspace/scratch/rama-next/rama-production.glb --blend games/yuga-native/art/production/reconstruction-rama.blend --manifest games/yuga-native/art/production/reconstruction-editable.json
python3 games/yuga-native/art/production/reconstruct_rama.py --output games/yuga-native/assets/heroes/rama-production.glb --manifest games/yuga-native/art/production/reconstruction-manifest.json --blend games/yuga-native/art/production/reconstruction-rama.blend --production-provenance
python3 games/yuga-native/tests/hero_reconstruction_cases.py --report games/yuga-native/art/production/reconstruction.validation.json
python3 games/yuga-native/art/production/validate_rama.py
```

The runtime GLB is byte-reproducible and two clean generations are checked. The compressed editable Blender file is a pinned generated artifact; Blender session metadata is not asserted byte-reproducible. General Blender re-export is not the supported runtime correction path and requires new rig/skin/animation equivalence checks. Artistic edits to the editable source do not automatically propagate into the deterministic surface generator.

Godot import and actual visual capture follow under the shared render/import owner. `tools/capture-hero-next.gd` provides five static material views: front, rear, face, linen folds and greater-distance studio contrast. Its report labels the studio staging; it is not actual gameplay. Integrated motion/world captures provide separate gameplay-scale context.

## Current evidence and limits

`reconstruction.validation.json` records six focused gates: exact rig/skin/geometry/animation preservation, finite bounded new colours and valid image CRCs, byte-identical regeneration, rejection of changed baseline input, rejection of original binary mutation, rejection of corrupted generated PNG data, and encoded palette bounds that reject the pale first surface pass (the first gate groups the related structural assertions). The existing Rama structural validator also passes. It retains the predecessor's 45 bounded pose records as historical data; it does not relabel those as newly rendered samples.

The new Blender reconstruction evaluated nine evenly spaced poses across each of nine actions: 81 finite bounded skinned-mesh/bone samples. These checks do not establish continuous motion quality, intersections, foot contact, grip quality, realistic cloth, anatomy, expression or concept likeness. Actual front/face/rear and gameplay render review remains required before accepting a visual improvement. This packet does not establish commercial-game or AAA art quality, a complete native hero roster, online authority or hero health/death.
