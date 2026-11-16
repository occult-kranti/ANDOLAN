# CONTENT10-READONLY-QA-01

**Current combined-build qualification is blocked by a stable Sangam source/specification mismatch.** The existing map suite exits 1 on its first imported-district installation check. All monitored source hashes remain identical before and after that run, so this is not labelled an in-run transient.

[Receipt r1](receipt-r1.json), [original Godot result](sangam-district-r1.json), [log](sangam-district-r1.log), [before hashes](sources-before.json) and [after hashes](sources-after.json) preserve the exact failing source identity and command. No source, shared test, checker, import, render or export was changed or launched by this review; the existing test ran headless with isolated user data.

A later source inspection found adapter/spec changes between runs. The bounded [r2 receipt](receipt-r2.json), [Godot result](sangam-district-r2.json) and [log](sangam-district-r2.log) preserve a second stable failure with the same mismatched shader/authoring pins. The corrected deferred [direct adapter guard probe](install-guard-probe-r2.json) confirms the actual rejection reason `finish_shader_hash` on adapter `4bc793ca04f17ef4e9f3e3e2992551a55b7c90ff1e3b7fd67ba9bf835654df1e`, spec `e5747a11871c7cc3735d9516dd78855beb8f639f8a3e7adfbc97a489b0fa5ba2` and shader `c8e455ca0e0a80cc1e21ff809f5afdcb365f2d8668bb1b7b54ef586798eb9d07`. The first direct probe ran too early during SceneTree initialization and rejected its not-yet-active host; it is retained as a probe setup failure and excluded from installation evidence. No additional blind retries are used to conceal either stable map failure.

| Item | Result |
| --- | --- |
| Existing `tests/sangam_district_cases.gd` | Exit 1; first installation assertion fails before further physics checks execute |
| Source before/after | Identical across 33 monitored paths |
| Base map / GLB / editable blend pins | Match specification |
| Twelve inherited texture pins | All match specification |
| Native profile | Content10, 19 enumerated sources |
| Prior authority pins | All 17 content9 pins retained unchanged; only adapter/spec paths added |
| Browser/proposal / wire/coordinates/limits | Unchanged relative to preserved content9 catalogue |
| Finish shader pin | **Mismatch**: expected `fb90a037589caf756997cf6d1abfe3ad7e9ce452f0d2c97a5f4b876517ae8184`, actual `c8e455ca0e0a80cc1e21ff809f5afdcb365f2d8668bb1b7b54ef586798eb9d07` |
| Authoring script pin | **Mismatch**: expected `ae8afc988f271f4d5fb0afe0ece7309506ab3d7a3d20555c89a0795741d6b249`, actual `a01e4e8741860c3bb9e082408bb97c9b15e0dff54d436839d92b7245d5893fa5` |

The two mismatched actual files share modification time `2026-11-16T00:23:30.083662Z`. `SangamDistrict.build()` explicitly rejects a mismatch between the current finish shader and `finish_shader_sha256` before adding geometry or publishing replacement colliders. The integrated world defaults `sangam_district_enabled` to true; `_build_sangam_district()` returns false on that rejection, and `_ready()` returns before completing the world. Thus ledger/hash consistency alone cannot qualify startup. Root and the frozen build owner received this finding immediately. They own stabilization/correction and any subsequent rerun; this reviewer did not rewrite pins to conceal the rejection.

## Source review and intended boundaries

The adapter is an original native-only visual/collision addition. It requires an identity-transformed host and eight expected original city blocks/collider locations. It preserves original node/collider identities, replaces their shapes with their declared full-solid box footprints, hides superseded art, and stores enough state to restore previous shapes/transforms/visibility/layers. Publication occurs only after its imported counts/materials and four cover dimensions pass. The budget is 308,422 triangles, 26 imported mesh instances, eight inherited building footprints, ten overhead collision bodies and four additional ground-cover bodies. These are measured/count assertions, not physical-GPU performance or complete art acceptance.

The adapter does not replace the continuous floor. Grounded movement retains the native floor and existing eight declared solid envelopes. Four 3×2.7×6 m cover footprints are added at x±8/z±60 to both actual 3D collision and a deep-copied army manifest. `prepare_army_manifest()` rejects duplicate cover application, transformed district roots and corrupted cover metadata. Overhead triangles are deliberately absent from the planar army collision list, preserving the central grounded lane under two galleries. These intended behaviors are directly covered by the existing test source, but **the current failing run did not reach those checks**. Their prior passage elsewhere is not substituted for this source-bound failure.

The integrated world builds Lanka gate/garden first, then Sangam, then derives army collision in sequence from gate, garden and Sangam before configuring the army. The isolated Sangam suite constructs a matching eight-block host and checks native rays, army line clearance, grounded cast acceptance, elevated-cast rejection and reversible removal. It does not itself execute the combined gate/garden/Sangam/shop scene, natural minion route completion, relay supplies, shop distances, actual player navigation, rendered telegraph visibility, PCK remapping or performance. Root's frozen-build combined map/shop checks and actual rendered/package journey remain required. The earlier shop/result QA only applies to the exact hashes in its own receipts.

The `sangam_district_enabled` source flag offers a separate disabled path, but it is currently true by default; this review does not silently recommend changing or advertising the disabled baseline as the new map. Runtime metadata labels Sangam native-only and does not claim online or elevated hero combat. The real Rama kit rejects the elevated gallery origin in the intended tests; a walkable deck is not proof of elevated combat support.

## Asset provenance review

`art/sangam-district/README.md`, `manifest.json`, the runtime specification and `tools/studio/build_sangam_district.py` describe original project geometry/code. The authoring source uses Blender primitives/mesh construction and existing project PBR inputs; no game files, photographs, downloaded meshes or add-ons were observed in the reviewed authoring input path. The twelve texture files match the exact existing courtyard source hashes. `art/README.md` dedicates that courtyard geometry/texture set to CC0; `NOTICE/ASSET-NOTICE.md` preserves the project's provenance distinction and third-party hero/tool notices. This is source/notice evidence, not an independent audit of every historical upstream asset. No new third-party credit omission was identified in these inspected map inputs.

The Sangam source README records rejected runs, the editable blend and native material-finish scope. Its current authoring-script mismatch must be resolved before describing the current script as the exact rebuild source of the accepted GLB. The new geometry/code is described as original project work; engine/tool licenses are not treated as asset licenses. The canonical packager copies native notices, but the new map's full authoring script lives outside the native tree at `tools/studio/build_sangam_district.py`; the build owner was told to retain it if claiming reproducible authoring provenance.

Next owner: root / frozen-build owner. Preserve r1, stabilize a coherent specification and actual files, rerun the existing isolated map suite, then qualify the combined shop/map scene and the actual exported build. No complete-map, playable-route, visual-parity or hardware-performance acceptance is granted here.
