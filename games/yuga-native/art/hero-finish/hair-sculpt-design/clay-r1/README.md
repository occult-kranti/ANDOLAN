# Editable whole-hair coarse clay — one design

The approved concept direction is a gathered sweep with overlapping asymmetric S falls, with its tall upright knot lowered into a compact folded gather. This packet stops at one coarse surface. The first interpolated fall-root fit failed and is retained; one local root seating correction produced the current cage. No alternative hairstyle, fine strands, UVs, LODs or GLB was made.

`master-cage.json` and `master-cage.obj` are the editable cage in glTF metres. The authoring .blend is at `/workspace/scratch/yuga-hair-clay-r1/clay-save-r1/whole-hair-clay.blend`, SHA-256 `b2bcea87e5aacf7ec49dae44df915063223bfa4b990ccb448457385008470475`. It contains the selected editable hair, named region groups, non-applied subdivision/thickness, and locked reference anatomy/brows/crown/tie/clothing/props from accepted UV parent `db4b2ec7…`. The original GLB is unchanged. See [shape notes](SHAPE_NOTES.md).

The cage has one shared-edge surface: scalp-to-gather-to-fold continuity, and two broad posterior falls rooted in the same hairline. This is not a set of intersecting tubes or another cap/connector union. The new fold reaches 1.900 m, about 20 mm below the original knot. The lower end reaches 1.508 m; this new length has no inherited action-clearance qualification.

The Blender save ran on CPU3, background, one thread, in Blender 4.3.2: exit 0 in 2.86 seconds, no warnings/errors, no render/import/export. Rest-space cage checks and checks of the **actual evaluated subdivision1 + inward 2 mm thickness** each pass 12/12. Evaluated minimum distances are 2.129 mm to reference head/face and 0.819 mm to fixed head gold/gems; nearby clothing/quiver is at least 8 mm away in the checked rest extraction. These are rest geometry facts, not visual acceptance or motion safety.

The source cage's initial local fit failure (58 head/neck crossing pairs) and exact executed sources are preserved under `docs/evidence/desktop-finish/hair-sculpt-design/W2-clay-r1/retained-first-fit-failure/`. The seated/evaluated reports and actual Blender save log are adjacent. The evaluated scene deliberately uses subdivision1 for both editing and rendering, overriding the initial cage metadata's suggested render2; the evaluated JSON/report and saved scene pin the actual setup.

W1 owns the next engine lane. `capture_clay.UNRUN.py` is a prepared, unexecuted four-view authoring capture, with projection preflight and exact .blend admission. It uses the four saved cameras and changes no mesh/material/light/camera transforms. The fourth view is a **rest-space cast-angle design view**, not the animated public cast. All four actual clay images must be reviewed before UVs, fine detail or GLBs. Fine work must also repeat complete head/crown, cloth/bow, all poses and secondary checks later.

Prepared W1 commands (not run by W2):

```sh
blender --background /workspace/scratch/yuga-hair-clay-r1/clay-save-r1/whole-hair-clay.blend --threads 2 --python /workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-r1/capture_clay.UNRUN.py -- --output /workspace/scratch/yuga-hair-clay-r1/preflight-r1 --preflight
blender --background /workspace/scratch/yuga-hair-clay-r1/clay-save-r1/whole-hair-clay.blend --threads 2 --python /workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-r1/capture_clay.UNRUN.py -- --output /workspace/scratch/yuga-hair-clay-r1/render-r1
```

Do not accept the hairstyle from connectivity, counts or these contact results. Actual clay silhouette/flow review remains open. The canonical hero, rig, accepted materials/UVs, and all rejected R4–R6 packets are untouched.
