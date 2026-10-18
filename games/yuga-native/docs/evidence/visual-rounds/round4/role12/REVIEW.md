# R4-12 — actual imported skin versus capsule and ground

**Measurement accepted; motion/contact acceptance remains open.** The promoted R7 runtime produced 476 actual physics samples through the courtyard route, gallery jump, and Confluence deck fall/jump. The final modifier pose and body collision state were captured in the same callback. Native checks pass 15/15; nine independent measurement checks pass. No runtime source or asset was changed. No import or 3D render was run, and no new framebuffer was judged.

Work began at HEAD `a43d5d8e71fc16363fb6163ce856ccf325dd437f`; shared HEAD had advanced to `495fae3aad59bfcce22506cc27f9d042741cd4ab` when the receipt was written. Exact runtime source/cache hashes identify the run, rather than a clean-commit claim. The promoted near/mid/far sources match the exact R3 promotion receipt; every imported source MD5 is fresh and all pinned sources/cache bytes stay unchanged during execution. The motion controller remains `4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1`.

## Actual measurements

The selector uses imported rest y<0.30 m and summed named foot/toe weight>0.5 per side. The actual visible near mesh supplies 6,790 vertices per side: gold899, leather1334 and skin4557. All nine near/mid/far material parts are archived; near alone was visible in these fixtures. Selected meshes have no blend shapes and identity mesh-to-rig transform. Actual selected shader displacement is zero. Named inverse binds, all164 final bone transforms, live rig transform, capsule, camera, foot targets and per-part visibility/offsets are retained.

| Measurement | Actual result |
| --- | --- |
| Grounded unlocked left sole, route sample91 | −24.744474 mm; 3,403 selected vertices below−5 mm |
| Grounded side-samples below−5 mm |34 of704; all unlocked |
| Maximum same original planted-vertex drift |3.055982 mm, left samples166→170 |
| Original planted target drift during each same lock |0 m |
| Locked sole minimum after initial samples0–13 |0.670221 to1.409563 mm |
| Maximum selected sole world step |183.521288 mm between60 Hz samples21→22, right; finite step includes motion, not a C0/C1 proof |
| Native camera whole-sole numerical bounds |(382.513,711.595)–(636.345,870.792), inside24 px at1280×960 |

At the strict penetration witness, the actual capsule is radius0.29 m, height1.8 m, centered0.9 m above its root; its bottom is about0.1 mm over `CourtyardFloor`. The collision plane is y0 with normalUP. A valid capsule contact therefore coexists with actual imported skin below the plane. This is a concrete current-runtime limitation, consistent with earlier source-only and rejected motion studies; it is not evidence of a new R7 geometry regression.

The initial title/fixture state retains a50.570461 mm locked-foot clearance for13 samples. Fixture placement changed the root without establishing a new plant; this is retained separately from ordinary gait. The first gallery sample retains the previous slide contact at y0 after placement at y0.44. Its capsule is not on that old plane and the analysis excludes it from capsule-plane-coincident statistics. These boundaries must not be silently treated as settled contact or erased by moving original anchors.

## Evidence and reproduction

`probe_imported_contact.gd` uses actual scenes, real Input actions and normal physics. It makes only initial fixture placements, with no per-frame root, velocity or pose corrections. Existing R4-02 route/jump checks are retained. The corrected run exits0 with478 final modifier callbacks and476 samples. `test-receipt.json` contains the exact command, source/cache hashes and promotion checks. `actual-imported-contact-r2.json.gz` contains the full tape; `actual-imported-sole-selector.json` provides exact imported per-surface indices and bind-name order for role06 reuse. `analyze_imported_contact.py` skins those actual arrays and records all per-side minima, original anchors and camera projections.

The first observer read body state after `process_frame`, exactly one physics frame newer than the final modifier snapshot in476/476 samples. Its failed receipt, raw compressed tape, log and original helper remain as r1 evidence. The corrected observer captures body/collision state inside `modification_processed`; all476 pose/body frame identities match. Reproduce numeric analysis with:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/docs/evidence/visual-rounds/round4/role12/analyze_imported_contact.py games/yuga-native/docs/evidence/visual-rounds/round4/role12/actual-imported-contact-r2.json.gz /tmp/r4-imported-contact-analysis.json
```

## Remaining gate and handoff

This is actual imported CPU skinning with native final modifier snapshots, not GPU-deformed vertex capture or rendered foot/shadow evidence. Flat support planes, a fixed65° native camera and near LOD were measured. Full actor/weapon visibility, non-flat support, LOD transitions, all release/cancel boundaries, normal-speed continuity and hardware FPS remain open. Role06 should reuse the selector and same-callback observer in its single uninterrupted runtime tape, preserving exact original anchors and contact-state transitions. No shadow, exposure, material, animation or contact correction is proposed by this role.
