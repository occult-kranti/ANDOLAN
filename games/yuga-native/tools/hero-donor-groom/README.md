# Donor hair authoring intake

[Actual source/mask/scaffold checkpoint](../../art/hero-donor-groom-oct23/README.md). Original generated geometry and donor files remain immutable. This tool packet produced an **unfitted authoring scaffold**, not a clean replacement hero.

- `inspect_sources.py`: exact donor components/face IDs and generated rear albedo-region inventory.
- `freeze_mask.py`: conservative face-ID proposal, full protected complement and every selected corner's XYZ/UV/RGB. The proposal was rejected.
- `check_mask_interiors.py`: independent WebP decode / corner cross-check, edge/centroid/grid adverse witnesses.
- `raster_mask.py`: every covered UV texel via triangle-square SAT, bilinear support guard and exact-coordinate edge-component fragmentation. Passing color checks never implies semantic permission.
- `render_mask.py`: three actual source-mask diagnostic views, no removal/fitting. Requires root's heavy render lane.
- `stage_scaffold.py`: exact donor component 1 extraction, packed material reuse, one low-poly editing seed, measured donor-only anchors, complete generated reference and UNKNOWN face-label template.
- `verify_scaffold.py`: cold reopen and eighteen source/donor/UV/image/rig/template checks.

All Blender operations use `--python-exit-code 1`. Render at max two threads; data-only operations use one. Supply fresh output directories. The known meaningful failed first scaffold validation and final positive receipts are retained in the art packet. No GLB exporter is provided because omission and coarse-form acceptance failed before that gate.
