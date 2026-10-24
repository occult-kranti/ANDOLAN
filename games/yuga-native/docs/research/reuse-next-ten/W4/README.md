# W4 — reuse-first Lanka lane gate

Latest frozen boundary and actual packaged 13/13 proof: [FINAL_HANDOFF.md](FINAL_HANDOFF.md).

This packet assembles one section of the actual Ghat promenade from existing original CC0 courtyard geometry. It does not replace the entire map or establish commercial-game visual quality. The single gate is now integrated by default; combined-source journey/export checks remain separate.

The previous intake selected `COL_BEVEL_Warm_carved_sandstone`: that material aggregate spans the whole courtyard, rather than a single pillar. The new preparation step selects **241 whole position-welded connected pieces** already inside the existing gate region. No triangle is clipped, no new box architecture is generated and no source UV, normal, tangent or material is redesigned. The selection contains **17,862 triangles, 11 mesh/material surfaces and 6,706 structural collision triangles**. One exact static triangle body provides the actual opening; decorative source groups never gain collision.

- Source: `assets/environment/lanka_courtyard.glb`, SHA256 `1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33`, 17,036,264 bytes.
- Licence: existing `assets/environment/lanka_courtyard.metadata.json` explicitly grants CC0-1.0 to this original generated geometry and textures; generator remains under repository licensing. No commercial game art or third-party model is used.
- Units: original GLB metres, Y-up; original ground y=0. Source gate centre `(0,0,-24.8)` moves rigidly to `(-40,0,-54)`. No scale, reflection or extra axis conversion.
- Placement: the gate crosses the Ghat promenade, preserving its full eight metre clear lane and existing army centre/offset routes. Side piers provide real eye-height cover. Its source carved front faces south; the opposite source face has quiet stone rather than invented matching ornament.
- Assets: source GLB is read through a scratch symlink; **zero source GLB bytes are copied by intake**. The existing native `GLTFDocument` loader is reused from `tools/map-reuse-intake/map_loader.gd`, itself adapted from `tools/reuse-vfx-stage/source_loader.gd`.

## Actual checks and failures

The isolated fixture passed **22 checks** (the original 18 plus four malformed-selection-field controls): whole-source selection cost, native metre bounds, exact visual/collider triangles, 365 actual-Confluence capsule-route samples across five traces, actual pier interiors, opening/cover/crown sightlines, 73 swept shoulder-camera spheres, sampled selected-surface rays, source mutation checks and malformed selections. An injected full gate AABB demonstrably blocks the opening; removing it restores passage. The initial JSON-number/array type contract error and an exactly-on-arch-boundary ray failure are retained in scratch, with the corrected explicit contract/probe.

The loaded canonical-world preflight passed **27 checks**. It checks the actual Confluence capsule (radius 0.65 m,height 1.8 m), the base training-player 0.29 m comparison, **730** route positions, **615** existing army-role radius/2.2 m margin-trace probes, clear opening LOS and all preexisting static-body identities. Only one new static body is added. Injecting an old broad box is detected in this full world as well. The base player script's 0.29 m radius is overridden by the Confluence manifest before use; the packet does not confuse them.

Actual Forward+ software-Vulkan R1 completed **80 images / 43 checks** in **162.704 s** on qualified Godot 4.6.3 runtime SHA `e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e`. Current world source SHA was `dc14b21eba1570e58acc1664a9d6a75bd8ff02def71dc8cc195a3d613629018e`, including W2 HUD edits already present before capture; pre/post hashes match. This is llvmpipe evidence, not GPU frame-rate evidence.

The eight R1 stills are diagnostic: the held hero was frozen before evaluating its initial native idle and remains in the import A-pose. They cannot serve as polished public previews. The **72 advancing route frames** explicitly call the existing player's motion update and `rama_motion.evaluate_pose()` under the callback hold. They contain 72 distinct actual skeletal-pose hashes, finite native motion and actual `CharacterBody3D.move_and_collide` sweeps from z-64 to z-45.0667 at 8 m/s with no collision. The real shoulder spring camera follows. This is scripted staged traversal, not human-input testing; the army remains held for comparison. A parse/API diagnostic and the initial unchanged-pose failure are preserved before that correction.

A separate two-view correction evaluates the existing stationary production motion before pinning state, then uses the actual ordinary southbound camera at feet`(-40,.04,-32)`,yaw 0,pitch-.10. Those views show the source carved front. They are new views, never relabelled as northbound baseline pairs. The correction completed **two actual originals / 18 checks** in **56.347 s**; its preflight passed 14. Independent source/art review accepts this single gate for integration. No whole-map, general animation or hardware acceptance follows.

## Reproduce

From repository root, choose a fresh outside-checkout path:

```sh
python games/yuga-native/tools/map-reuse-placement/prepare.py --output /workspace/scratch/W4-fresh
/usr/local/bin/godot --headless --path /workspace/scratch/W4-fresh --script tools/map-reuse-placement/test_placement.gd
/usr/local/bin/godot --headless --path games/yuga-native --script tools/map-reuse-placement/capture.gd -- --preflight --selection=/workspace/scratch/W4-fresh/selection.json --output=/workspace/scratch/W4-context-fresh
```

Only the root-granted render owner may run `capture.py`; use the existing audited runtime and `--godot` qualified binary. It owns one Xvfb display, caps Mesa/OMP to 2 threads, enforces a fresh output and a bounded timeout, checks real image hashes/dimensions plus all native errors, and stops only its own two processes. Use `--ordinary-correction` for the separate two-image southbound/idle correction. Preserve meaningful failure directories.

## Conditional next stages

1. **Source selection:** complete gate pieces, licence/units/selection hashes and actual costs. Complete for this slice.
2. **Isolated physical opening:** capsule/camera/LOS plus real duplicate blocker negative. Complete for this slice.
3. **Context:** actual native world, unchanged body identities and army widths; ordinary day/night plus moving route. Physics/route complete; corrected idle art review pending.
4. **Independent review:** disconfirm wrong source IDs/transform, partial islands, hidden broad blockers and relevant nearby collision; inspect original frames. Accepted for this one gate, with the R1 staging limitation preserved and PCK identity still required.
5. **Runtime resource:** bake only the selected existing geometry into a compact standard native asset and prove reload attribute/geometry/collision correspondence. No whole-courtyard parse at each gameplay load. Complete: native compressed scene 3,793,793 bytes; 17 source/cache/lifecycle checks pass, plus 6 independent clean-rebuild equivalence checks. Exact input arrays, native material properties, 12 image byte hashes and original collision faces are preserved; zero external dependencies. A first 83 micrometre collider drift failure is retained and fixed by carrying the original raw collision faces as lossless native metadata rather than re-decompressing render meshes.
6. **Canonical helper:** root leases one named world helper and ready-time call; no change to eight original authority solids, all decks/anchors, map/army economy or browser authority. Fail closed on missing/wrong candidate, prevent duplicate call, expose one scoped report. Complete: production helper/call enabled by default,23 canonical-positive checks. Legacy 29 floor-envelope checks explicitly disable only the gate; strict 40 resource checks remain unchanged.
7. **Ordinary gameplay:** human input through the gate in both directions, shooting/LOS and practical camera/focus/menus with the integrated build. Open.
8. **Cost and distance:** actual ordinary/mid/far temporal/LOD review and physical-GPU frame/memory measurements. Open; current software timings establish only execution.
9. **District module adoption:** compare the next distinct courtyard/gallery/nature pieces against actual footprints and routes. One gate must not become a repeated full-map reskin. Open.
10. **Authority and release:** native-only shape contract stays explicit until corresponding server/elevation work is accepted; export/asset inclusion, final source pins and launch checks must pass before shipping. Open.

## Final integration and army-cover correction

The accepted gate now loads from normal `res://assets/world/lanka-lane-gate.scn` through `scripts/lanka_lane_gate.gd`; runtime code has no tool or scratch dependency. The helper caches the native scene, shares 11 meshes/sixmaterials and uniquely owns each collider. `confluence_world.gd` adds only the gate construction/report plus the private army configuration copy. Existing HUD/layout changes are preserved.

Actual integration testing found the existing army's planar LOS could shoot through the new native piers. The original failure is retained. Ten conservative source-component ground bounds now travel through **a deep copy of the manifest to the existing unchanged army.configure API**: two main plinths, six column feet and two collidable lantern pedestals. The large overhead arch never becomes a filled box. Containment covers 1,936 source ground triangles, and 956 sampled points each contact actual solid geometry for the smallest army 0.39 m capsule. Copy isolation, duplicate refusal, pier attacks/opening, all roles/offsets, reset/reconfigure and omitted-copy negative pass 14 checks. The original file/dictionary and army script remain unchanged.

The default world contains 35 army geometry boxes: original 8 authority+8 decks+9 existing relay-art footprints+10 new gate ground pieces. An initial integrated test expected 26 and correctly failed; its strict oracle was corrected to include the independently inspected existing relay additions. All 23 canonical integration checks now pass, including all lane/rotation sweeps,146 actual shoulder-camera sphere sweeps,730 hero/base capsule positions,615 margin-role probes plus 615 actual-formation role probes, unchanged 8 authority/8 deck/10 anchor identities, duplicate caller, real broad-box counterexample and fresh default caller. The legacy 29 physics checks and 40 strict resource checks also pass. The authoritative command/report handoff is in `execution.json`.

The mesh/material/texture/native-collision data is unchanged from accepted actual views. Added metadata and canonical integration are source/physics qualified; the current combined HUD/motion source requires its own ordinary journey capture. The external package probe must run against a real exported PCK, where exact `.scn` FileAccess/hash and private army-copy resolution are checked. No source-only package acceptance is inferred.
