# Sculpting the swept mane and tail

The new hair grows from the existing 167-joint Hanuman. The copper crest parts slightly off center, fans over the brow band and overlaps a darker mantle at the nape. Behind the ears the shorter cheek tufts preserve the face outline. The distal brush grows wider through the outer bend and narrows at the tip. The underlying tail remains continuous. [Character sheet](../../four-hero-motion/media/art/hanuman.png) · [Portrait target](hanuman-portrait-target.webp)

## Editable assets

Import the complete GLB into Blender for the weighted character, costume and eleven animation clips. Open the small Blender groom file to edit the five regions independently in rest space. It includes the actual copper fibers, their UVs, pigment attributes and skin-weight groups. The parameter file defines crown layers, nape fall, branch density, brush shape and muzzle fit. To carry a design change into the reproducible release, edit those guides or their curve generator and rebuild. Hand edits inside the separate Blender file require their own export. [Complete character](../models/hanuman-enhanced.glb) · [Editable groom](../models/hanuman-groom.blend) · [Guide parameters](groom.json) · [Sculpt code](../tools/sculpt.py)

| Weighted region | Locks | Vertices | Triangles | Contact |
| --- | ---: | ---: | ---: | --- |
| Crown | 68 | 6,120 | 9,792 | The ray-fitted scalp under the tilted hair part |
| Nape | 58 | 5,220 | 8,352 | The scalp and upper neck, blended to head, neck03 and neck02 |
| Cheeks | 44 | 3,960 | 6,336 | The source skin surface along the temple and lower cheek |
| Brows | 26 | 2,340 | 3,744 | The skin above the eye openings, clear of the tilak |
| Distal tail | 65 | 5,850 | 9,360 | Adjacent tail_03 and tail_04 joints |

In the exported character these five regions share one indexed draw. Their separate vertex and triangle ranges remain in the primitive’s glTF extras. Eight-sample cross-sections carry a curved ridge, a longitudinal cuticle texture and color that changes from root to tip. The solid geometry contributes to the shadow and silhouette when viewed from either side. The source guide for the articulated tail comes from the existing native Blender builder. [Native tail guide](../../../tools/hanuman-art/build.py) · [Counts and changed substrates](../evidence/sculpt.json)

## Face and motion

The original snout extends farther forward than the target portrait. A smooth three-dimensional deformation retracts it by up to 67.3 mm, widens the forward jaw and carries its fitted lip and nostril details through the same transform. The gradient transforms normals and tangents. The three affected materials account for 1,352 moved vertices, with original skin weights, UVs, indices, seams and facial joints. The eye openings and ritual pigment lie beyond the affected region. The existing area around the mouth still has the source mesh’s relatively smooth surface. [Fit and raw donor digest](../evidence/sculpt.json)

## Rebuild

From the repository root, run the following with Blender 4.3, Pillow and NumPy available.

```sh
python games/yuga-native/art/hanuman-hero-finish/tools/finish.py
```

The build first checks the pinned donor GLB. Blender fits the groom to the donor in rest coordinates and appends the new attributes to its original binary. The surface pass then builds the embedded material maps. The last pass reshapes four existing Mountain Pulse tail rotation curves after impact. The resulting GLB uses the playable character’s original skeleton and animation names. The separate studio source records its own digest and the playable GLB has a reproducible digest. [Pipeline](../tools/finish.py) · [Material pass](../tools/surfaces.py) · [Tail motion](../tools/motion.py) · [Build receipt](../evidence/build.json)
