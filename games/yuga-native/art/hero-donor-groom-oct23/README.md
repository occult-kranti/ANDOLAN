# Rear-hair authoring intake: rejected mask, retained clean donor

**No generated-source faces were removed and no replacement was fitted.** Actual rear and both rear-oblique diagnostic images plus independent review reject the automatic omission proposal. A useful rigless donor editing scaffold was saved and cold-reopened; the hero art gate remains open.

| Bounded subgoal | Actual result |
| --- | --- |
| 1. Freeze source-specific mask and protected complement | 2,342 face-ID proposals; 94,318 protected faces, including 1,812 mixed-corner triangles. Every proposed triangle has recorded original XYZ, UV and corner RGB. An independent interior/edge test rejects 188 proposals; the complete texel/support test rejects **1,226**. No omission is allowed. |
| 2. Reuse an exact clean donor region | Extracted only component 1 of the pre-C1 CC0 **Unified swept hair sculpture**: **12,762 vertices / 25,528 faces**, closed and manifold, original positions/UV/PBR retained. Created a **253-vertex / 510-triangle editable reduction seed** and six measured donor-only anchor suggestions. No source alignment or new gesture was authored. |
| 3. Actual review and saved intake | Three source-mask frames completed in 106.24 s. Independent quality rejected the interleaved hair/cape mask. The unfitted scene cold-reopened with **18/18 checks passing**. Four replacement clay views, texture/export, rigging and runtime promotion were not run because the removal gate failed. |

[Decision and exact pins](decision.json) · [full texel diagnostic](mask/full-texel-raster.json) · [source-mask render receipt](views/receipt.json) · [scaffold inventory](donor/scaffold.json) · [cold-reopen proof](donor/reopened-verification.json).

Actual views: [rear](views/rear.png), [rear-left](views/rear-left.png), [rear-right](views/rear-right.png). **Red** is the rejected omission proposal; **amber** is mixed-corner geometry that stayed protected. All 96,660 source triangles remain present in these diagnostics. Color classification is eligibility evidence, not a semantic label.

The full test uses triangle/texel-square separating axes, including boundary touches, followed by a conservative one-texel bilinear support guard. It checks 23,935 covered and 69,029 support texels, not just finite selected UV points. All 188 coarse failures are caught. The remaining 1,116 color-eligible faces form **103 exact-coordinate edge components**, largest 259 faces (23.2%), with 1,067 boundary edges. Removing the 188 earlier counterexamples does not produce a coherent, approved groom region. Filtering these counts further cannot establish where hair ends and cape/neck begins.

## Actual editable source

The scratch master is `/workspace/scratch/hero-donor-groom-oct23/scaffold-r3/unfitted-donor-scaffold.blend`, 14,176,333 bytes, SHA-256 **`c3ca6b9ba3f8352a36d7c53c562334f87679832f7391e94bc90ad1ef5594e0e9`**. No large `.blend` or duplicate GLB is committed. The retained recipe and original sources reproduce its contents; a fresh Blender save can have different container bytes, so verify its geometry/material contracts again.

The scene contains the complete unchanged generated source, the exact donor rear/nape at its **original donor coordinates**, its low-poly seed, and six measured donor vertex anchors. Both donor surfaces are hidden from rendering and remain unfitted. Their scale/position difference is intentional intake evidence. No donor rig or source anatomy is copied. The reduction seed is a single donor-only collapse at ratio 0.02; it is **not hand-authored quad retopology or an accepted silhouette**. Dense original donor face/vertex IDs, anchor XYZ and source/material image hashes are in scaffold.json.

The generated reference retains its original 93,214 vertices, 96,660 triangles, UVs and embedded image bytes. It additionally has stable `original_source_face_id` and `artist_semantic_label` face attributes. Every label starts **UNKNOWN**: `0 UNKNOWN`, `1 HAIR`, `2 CLOTH`, `3 SKIN`, `4 HARDWARE`, `5 UNCERTAIN`. The cold-reopen checker verifies exact original geometry/UV/images, stable IDs, unknown labels, donor IDs/materials, rig absence and seed geometry. It does not approve art.

The failed first scaffold validation is retained in logs: a stale Blender UV-layer handle after custom-attribute allocation failed the preservation assertion. The final script refreshes the layer lookup; the final saved scene passed exact source UV checks and the separate cold reopen. No failed scene was promoted.

## Next artist: label the boundary before fitting

Open a working copy of the master. Keep the donor objects hidden initially and enable selection of **GENERATED ORIGINAL reference DO NOT DELETE**. Inspect the rear, neck, both ear/shoulder edges and cape transition at close range. Label original faces as hair, cloth, skin, hardware or uncertain; keep UNKNOWN and UNCERTAIN faces protected. Record why every uncertain mixed region is unresolved. The rejected color proposals are diagnostic references only and must not be imported as truth.

In Blender, select a semantically identified group in Edit Mode, return to Object Mode, then use the Python Console to label that selection, for example hair:

```python
obj = bpy.data.objects['GENERATED ORIGINAL reference DO NOT DELETE']
labels = obj.data.attributes['artist_semantic_label']
for face in obj.data.polygons:
    if face.select:
        labels.data[face.index].value = 1
```

Save sorted original face IDs for each label, explicit unknown/uncertain sets and the protected complement. Retain the original source positions/UV/images and protected faces; do not delete body or cloth to make an insertion fit. Obtain a fresh actual rear/both-oblique/front mask review from the same studio. **Only after boundary approval**, register the donor through measured source/donor attachment landmarks, directly shape a small cage into two unequal flowing families, and request four locked clay views before detail, UV/export or rig transfer. Follow [the retained artist contour task](../hero-finish/hair-sculpt-design/clay-grouped-r1/NEXT_ARTIST_TASK.md); do not revive the rejected C1–C8 bulk generators.

## Reproduce the bounded intake

Use Blender 4.3.2 from the repository root. These commands use installed tools and retained sources; no downloads are needed. Supply fresh output directories. Extract the compressed inventory below or regenerate it first.

```sh
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-donor-groom/inspect_sources.py -- --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --donor games/yuga-native/art/hero-rama/rama-hero.blend --output /workspace/scratch/groom-intake-fresh
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-donor-groom/stage_scaffold.py -- --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --donor games/yuga-native/art/hero-rama/rama-hero.blend --inventory /workspace/scratch/groom-intake-fresh/inventory.json --output /workspace/scratch/groom-scaffold-fresh
```

The freeze-mask, adversarial checker, full-raster, three-view renderer and cold-reopen checker are retained in [the tool directory](../../tools/hero-donor-groom/). The renderer requires the root-coordinated heavy lane. Compressed JSON inputs preserve exact original bytes when decompressed; their source hashes are in decision.json and the manifest. The original source files remain immutable inputs, and all final source faces remain protected.
