# R3-01 cloth roughness source notice

The `woven-roughness-r3.png` texture and its continuous cosine bake are original
YUGA project work, authored 2026-10-17. No downloaded texture pixels or third-party
shader code are embedded in the bake. This notice records authorship and source
provenance; it does not add a third-party asset license or relicense project work.

The technique review consulted Material Maker 1.6, repository
`RodZill4/material-maker`, revision
`b4fcad06f0b13785de423c42b36406df605c8321`,
[`addons/material_maker/nodes/weave.mmg`](https://github.com/RodZill4/material-maker/blob/b4fcad06f0b13785de423c42b36406df605c8321/addons/material_maker/nodes/weave.mmg),
licensed MIT. This candidate does not translate its `oldweave` expression or
copy its graph. The concrete lesson adopted is a periodic warp/weft crossing
with even counts; this original bake uses continuous cosine fields and omits
that source's hard `step` gates. Material Maker was not executed. Its inspected
Godot 3 `SpatialMaterial` export template was not imported.

The existing finish texture was reviewed as a baseline. It is the previously
adopted Microsoft Sheen Cloth CC0 roughness derivative, pinned in
`source-manifest.json`; its source pixels are not used by this candidate.
Existing hero color, normals, geometry, rig, animation, jewelry and trim retain
their existing notices. This work claims neither historical textile authenticity
nor a physically measured silk BRDF.
