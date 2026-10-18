# Shoulder R7: minimal private import and four-view recipe

**Prepared only.** No project was staged, no engine/import/raster ran, and no canonical or sealed shoulder file changed. Package execution and the lead's hair-review queue retain priority. W1 owns every future engine invocation. [Exact argv arrays](commands.UNRUN.json) are ready; [inputs](inputs.json) pin their source, tools and engines.

Reuse `/tmp/yuga-hair-r5-review-r1/baseline`, marker `20aed49da1db66b48a2dcac9f0ced2afa9eb08753293a8bda943e7c256fab63e`. W1/W2 confirmed it contains the accepted sash-UV/smooth-crown hero, current motion `5023b301…`, world `42e617a3…`, and finish `6eb51ce8…`; **no proposed hair**. The [read-only readiness check](source-readiness.json) verified all 1,015 files and their shared import blobs, all six hero pins, and both engine payloads. Its 176 imports are retained, not reimported wholesale.

| LOD | Accepted baseline SHA-256 | Inactive shoulder R7 SHA-256 |
| --- | --- | --- |
| Near | `db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e` | `8755b65b1b103b3d3210993240c9e18c196510757e1b031bb684eb45e47b629b` |
| Mid | `b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005` | `8ae53f22a9536d7dcf3d9506906ac83e15222d0b9eadacd51cff82c7d7b43371` |
| Far | `aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a` | `5b382f97b64658784d15fbb6ef816af22c62d8148717b70c797dea8e2172be37` |

## Later execution order

1. Run `prepare.py import --work /tmp/yuga-shoulder-r7-review-r1`. It creates only a minimal three-GLB importer and cached baseline probe project. It copies the candidate raw trio **once, 99,384,992 bytes**, copies original import descriptors/settings, and removes only `run/main_scene`. Baseline resources use verified immutable hardlinks; mutable auxiliary caches are private copies. It never calls an engine. Additional generated cache storage is measured after import, not guessed now.
2. W1 runs the `import` argv from the command file: official editor `f64d4ed1…`, private candidate path, fresh XDG, CPU0,1, 120-second cap. Retain command, full log, exit status and generated resource/descriptor hashes. On failure preserve the attempt; do not retry automatically. No canonical or shared-store writes are allowed.
3. Run the two `probes`, then `compare_import`. These call the sealed shoulder resource probe and topology comparator directly. Require exact noncap complete attribute bytes, oriented triangle multiplicity, all 164 bones/binds, materials/textures, clips/morphs, 14 untouched surfaces and original descriptors. Only the four declared cap-containing material surfaces change. New POSITION/UV/topology and rigid49/alpha0 bindings are checked against source; decoded normal/tangent bounds remain the sealed explicit limits. Reversed/missing/extra triangles and signed-zero mutations must remain rejected. No relaxed multiset or frame check is proposed.
4. After that proof passes, run `prepare.py review --work …`. This hardlinks immutable source/cache into two independent marker inventories, reuses a content-addressed hardlink store, and copies only mutable auxiliary files. It requires exactly nine pair differences: three raw GLBs and their three SCN/MD5 pairs. The common helper is copied once. There is no repository clone or second raw-trio copy.
5. Run fresh baseline/candidate `preflight` commands and `compare_preflight`; then, only in W1's assigned raster slot, the two sequential `render` commands and `compare_render`. Both branches use exact `dce0422d…`, the same retained 112 Godot/101 Mesa seed policy, and 600/300-second overall/no-progress bounds. Proposed displays185/186 must be free. Preserve failures and source/store before/after proofs. The private runner adapter changes only the shoulder case/helper/environment/branch mapping from the sealed R5 runner.

The Python files passed AST parsing and input guards. **Staging phases, GDScript parsing, actual imported semantics, and report comparators remain unexecuted.** Fresh matched originals are mandatory; no older image is substituted.

## Four shots and strict comparison

The common [helper](shoulder_capture.gd) changes the sealed helper only in [two declared places](helper-changes.patch): current motion admission `8c377→5023`, and rest-profile visual yaw `0→180`. The latter turns the authored positive-X left shoulder toward the negative-X camera; identity model roots and the player's declared +Z authored front support this source-level choice. Actual visibility remains a pixel gate. Front/rear/cast cameras and all timing remain unchanged.

| Shot | Control |
| --- | --- |
| `rest-front` | Existing staged front, visual yaw−90°, FOV38° |
| `rest-profile` | Anatomical-left profile, yaw180°, same station/camera |
| `rest-rear` | Existing staged rear, yaw90°, FOV38° |
| `cast-three-quarter` | Actual Target03 aim and public Piercing Dawn, ~0.30-second nocked windup; actual final modifier pose |

All shots require near LOD and 24-pixel shoulder margins. Compare all164 final bone matrices, events, camera/light, face, LOD, secondary offsets and clocks exactly. The prepared view comparator permits only declared raw/branch/image/wall-cleanup fields, validated shoulder bounds/counts, and the changed cloth census derived from the actual imported gold/silk arrays. It does not align poses or excuse clock differences. Cleanup remains two bounded real mixer ticks after observations.

## Reject if these remain visible

- The outward compact plate floats, exposes an awkward inner-shoulder opening after the old cap is removed, or loses an understandable attachment. Inspect front and left profile together; projection bounds cannot prove occlusion or contact.
- Cap/lame roots cut into arm, torso or sash during the cast, or the bow/hand relationship becomes confused. Larger shells, hinge fits, and earlier compact candidates had retained draw/idle/recoil crossings; fewer intersections were not acceptance.
- Rolled edges and 3–3.5 mm walls read as thin sheets, or borrowed cobalt **silk** response makes the plate look rubbery. Judge a readable curved layer and restrained lotus, not added motif quantity.

The sealed 348-draw/37-pose/120-stress source proofs keep their original motion-tape scope; admission of `5023` does not transfer them to every newer transition. Only exact superseded cap triangles were excluded. Actor physics capsule, world/other actors, arbitrary morphs/transitions, decorative self-joins and unaccepted hair remain outside that proof. Current four-view native contact observations are still required; mid/far pixels, title-scale value and continuous shimmer remain later gates.

No hair composition or dead-prefix compaction occurs here. Any future accepted hair must be explicitly composed and requalified; it must not be silently overwritten by this accepted-UV-only shoulder trio. The current release excludes the shoulder. Keep the reusable baseline/store intact until W1 releases this recipe's dependency.
