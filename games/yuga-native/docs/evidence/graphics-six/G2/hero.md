# G2 / worker 01 — optional modeled upper-hair tier

**Candidate frozen for an off/on render; default activation is not authorized by this evidence.** I opened the G1 title day/night and world day originals, then `light-front.png`, `dark-profile.png` and `dark-rear.png` in `/tmp/yuga-g1-hero-r1/`. The long smooth nape lobes remain the concrete defect. More small metallic ornaments would not address it.

The new optional `RamaUpperHairLayers` helper builds seven broad, short swept layers, with staggered ends above the lower nape. The guide generator ray-fits the exact original R7 hair, then adds a small overlapping tier. Original guide source lives in `art/hero-finish/build_g2_hair_layers.py`; `assets/hero-finish/upper-hair-layers.json` pins source and generator hashes. This is separate from `RamaCharacterAccents`; the rejected temple wisps remain inactive and unchanged.

Cost is **1,904 triangles, 1,085 vertices, one ArrayMesh/MeshInstance3D and one head BoneAttachment3D**. It shares the existing hair material, adds no texture or material resource, and runs no process/physics callbacks or skeleton writes. The geometry is present at all distances in this review candidate; it introduces no new distance switch, and the constant additional far-LOD cost remains part of the later budget review. All added vertex RGB is white and semantic alpha is zero, so existing secondary offsets cannot move the upper tier independently of its head attachment. Normals, tangent directions and handedness are derived from actual tapered triangles; UV seam frames are joined without changing UVs.

Fresh native checks pass **26/26** against the current imported 164-bone hero and G1 maps: exact unchanged preexisting mesh/material resources and bone poses, finite nondegenerate geometry, packed unit/orthogonal TBN frames, UV/alpha contracts, three actual head-yaw samples, 100 idempotent calls, competing-owner rejection, release/reconfigure and transferred-node preservation. The first parse failure and overly strict fixture results are retained. ArrayMesh packing produced a maximum normal/tangent dot of about 0.00021, within the documented test bound 0.001; the head-driving fixture uses approximate transform equality only after its quaternion roundtrip. The helper's own zero-pose-write test uses exact equality.

The CPU full-triangle probe compares the actual Godot-generated mesh with every nonhair source surface, grouped into bow, skin/face, metal/gems and cloth/leather. Final source-rest minimum clearances are skin **3.638 mm**, metal **8.011 mm**, bow/cloth **at least 15 mm**. All **21 unique archived bone-matrix poses** have zero crossing pairs. The original side tips failed the historical Dawn Volley windup with 28 left-forearm crossing pairs; the exact guide/generator/report are preserved in `rejected-lower-side-tips/`. Only the two side layers were shortened/raised before the successful rerun. The old pose archive is used as historical stress input; this does not claim execution of current G2 actions, face morphs or secondary offsets. Fresh continuous-motion and LOD images remain separate gates.

Runtime source is **not activated**. Root's review overlay can use this after the existing LOD/calibration/secondary/finish binding, with identical clock/pose waits in both branches:

```gdscript
var layers = load("res://scripts/rama_upper_hair_layers.gd").new()
hero_visual.add_child(layers)
assert(layers.configure(hero_visual))
# Remove the candidate after review:
layers.release()
layers.free()
```

Capture at most six matched images: off/on rear, profile and front. Keep camera, light, head pose, distance, materials and all other changes identical. Accept only if the overlap creates readable layering and useful profile breakup. Reject/remove if it merely thickens the cap, resembles attached leaves, clips the raised arm/ear/diadem, or loses silhouette against the backdrop. Skin, cloth volume, foot support and lower-nape/collar contact remain open; this is no full groom/sculpt or commercial-quality claim.

Frozen identities: helper `989d069b1364e50a3ae31530f778659e5910ea1c3e05f7b81edccf90e3101732`; guides `181ecd859cc0569ca7ed5e4c48f60620a986189c730f3aff771ff3f51e562242`; generator `8b929a7b6481b8b95d611e90a10b8d8c80d70169ee8ff3fa087726dee4add934`; retained near GLB `8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c`. Exact check dependencies, guide/source hashes, pose identity, triangle witnesses and geometry are in `hero-rig-checks.json`, `hero-clearance.json` and `hero-geometry.json`. No player, motion, UI, world, source GLB or contract file was edited.
