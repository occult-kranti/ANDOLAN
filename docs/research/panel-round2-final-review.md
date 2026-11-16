# Independent round 2 review — actual launch captures and delivery claims

15 November 2026. Reviewer: game/source researcher. Root owns the new launch/briefing implementation, studio plan and source credits; build owner captured the native originals. This reviewer authored the separate N4 texture-sharing implementation, so **this report does not provide independent acceptance of N4**. No product sources, plan, notices or images were edited in this review; the output is this report.

## Actual images and source identity

Inspected original native screenshots directly, at 1280×720:

| Original | SHA-256 | Visual disposition |
| --- | --- | --- |
| `briefing-confluence.png` | `4e36f17c69fb339104cffa80cb09edbe8557e6cc1cb2a3e0f57070151d9228bb` | PASS for the bounded desktop launch composition: clear title/current hero, selected Confluence, truthful offline description, one gold launch action, subordinate lane schematic/first move/bindings, readable utilities. |
| `briefing-training.png` | `be381390f6eb521742841893173fcc5cec714f4a3320794bf906d5d225f863aa` | PASS for mode distinction: selected Bow training, changed action/target schematic/copy, retained live character and utilities. No clipping or overlap in this original. |
| `briefing-guide.png` | `08f783e40f1501bbd75f02f8a715a18e808dc1cbc2d1d4c54e9ff139a6b24963` | PASS for the inspected Kodanda guide state: readable two-column hierarchy, bow plus four abilities, visible LMB/Q/E/C/X labels, timing/range/context details and clear Back/Escape/F3 return. Scrollable content is visibly indicated. |

All three hashes match the build owner's [`briefing-review.json`](evidence/studio/toolchain/briefing-review.json). That receipt records actual XTest mouse/keyboard inputs: Confluence capture, click Bow training, F3 guide, Escape, Quit; the native process ended with exit 0. This reviewer inspected the images and receipt, not a new personally executed input journey. The receipt explicitly does not assert automated visual success or hardware performance.

The capture's [`briefing-source.json`](evidence/studio/toolchain/briefing-source.json) matches the inspected current source:

- `scripts/launch_shell.gd`: `9b1805d40fc11eecc21e86c23dab09cb38f4d0a79f48472b149ef63f0660ce36`.
- `scripts/launch_briefing.gd`: `a2a6027e5e7f94fb37486b5b7fa144e1ce4ec6967a1b11fd4d35de3e0b181e94`.

The separate [`contract-r3.json`](evidence/studio/briefing/contract-r3.json) passes eleven source-bound cases including current bindings, mode changes without launch/focus loss, returning from remap, loading/recovery, read-only focus and compact 100/150/200% scale behavior. Those cases support the controls contract. This review did **not** inspect actual 960×540 or enlarged-scale rendered originals, every ability detail, full match/result/reconnect, Windows or physical-GPU behavior; those remain outside these three screenshots.

## Image judgment and concept comparison

The actual title uses the existing rendered Rama and courtyard rather than substituting the AI painting. The character's body, bow/quiver and feet remain visible to the right of the scrim. Ivory text on the dark left field reads clearly; gold differentiates the primary action and selected state without making every control compete. The new schematic/binding strip is quieter than the primary action and does not conceal mode context or utilities. A selected mode and focus outline are visibly distinct. The guide uses an opaque surface and reinforces icon meanings with names and actual key labels.

The [`yuga-native-screen-targets.png`](../concepts/studio-2026-11-15/yuga-native-screen-targets.png) board has much richer anatomy/face/hair, fabric/metal treatment, city density and cinematic posing than the actual native character/courtyard. The real model still has simplified facial/hair surfaces, broad cloth shapes and restrained material detail; the static originals cannot establish convincing transition/contact/secondary motion. The sparse repeated architecture is also visibly less developed than the painting. These are existing production-art limits, not a reason to reject a functional, truthful launcher improvement or label the generated board implemented.

**Disposition: functional launch/guide presentation passes at the inspected desktop state; commercial hero-shooter art/motion quality remains LIMITED.** There is no observed evidence here for fourteen finished native heroes, online matches, full production maps or a complete final game. The optional briefing is a concrete implemented improvement toward that goal.

The board contains invented input/effect details, which its README explicitly rejects. Actual native defaults remain LMB Kodanda, Q Piercing Dawn, E Measured Step, C Guardian Circle and X Dawn Volley. Code uses `Bindings.label()` and refreshes when the title becomes visible, so saved bindings own displayed hints. The mode descriptions explicitly say offline practice as Rama. `relay_session.gd` actually supplies arrows to an eligible player at an owned/clear relay; the Confluence first move “hold relays for arrows” has a real implementation basis. The schematic does not claim exact path geometry or show live match state.

## Plan and notice review

Read `games/yuga-native/docs/STUDIO_PRODUCTION_PLAN.md`, `NOTICE/STUDIO_SOURCES.md`, current native PRODUCT/DESIGN, the design master's roster/rules migration, the concept README and tools owner's execution report. The proposed Sangam Accord narrative is explicitly new/planned; the six teaching beats are not represented as a delivered campaign. The plan separates native one-Rama offline availability, existing browser products, next native 3v3 and future 6v6/fourteen-hero/eighteen-minute release. Duplicate picks in the 3v3 slice and the later tower/core/tiebreak migration agree with the existing game-design master.

The Foundry is correctly described as a separate original Blender blockout and native walk/jump study, not an authoritative Confluence map or production-art acceptance. Source `studio_map_study.gd` uses a capsule walker, box/ramp collision and explicit “no capture/combat authority” copy. Its actual map imagery and traversal receipt require their separate build/review; this first review did not inspect them.

The source notice correctly distinguishes application licenses from exported original geometry; actual source checkouts from installed/executed tools; REA analysis from Raea rendering; GDQuest MIT code from excluded CC-BY-NC-SA art; and generated composition targets from shipped 3D assets. REA 6.5.0 static execution and no MCP registration are supported by the tools owner's receipt/report. No new reference code/art is claimed copied into the briefing/map. Existing font/MakeHuman/CC0/runtime notices remain applicable and are not replaced by the new studio notice.

Findings sent to root for correction (not edited by this reviewer):

1. **License wording:** the plan's sentence “Study Prometheus/OWLib … Preserve their AGPL obligations” incorrectly groups both licenses. Prometheus is AGPLv3; OWLib/DataTool is MIT; OWM is GPLv3. Each needs its own exact file/license scope if later code is adopted.
2. **Three local links:** from `games/yuga-native/docs/`, the AI-board README, source catalog and delivery report currently use four parent levels. They resolve above the repository. Use three parent levels to reach `docs/concepts/...`, `tools/research/...` and `docs/research/STUDIO_DELIVERY.md`. The delivery file must exist when linked as delivered evidence.

All other checked local plan/notice targets exist; the roster heading matches its anchor. Root owns these corrections. A final accepted document should link exact evidence rather than imply future plan gates have passed.

## Final scope and next owner

This is an independent visual/source review of the root-authored launcher and documentation, with the source-bound limits above. N4 remains this reviewer's own implementation and needs the build owner's independent combined-source review. The native final package, package notices, actual Foundry screenshot/traversal, all-mode regression and artifact identity remain the build owner's separate gates. The truthful delivery description is **a working native/browser checkpoint, original launch refinement, source/tool qualification, source-resource optimization and separate map prototype**, accompanied by a plan for the complete game.

## Independent artifact follow-up — local native ZIPs

The root corrected the license wording and all three relative paths in the current studio plan. Prometheus/OWLib/OWM now retain their separate AGPLv3/MIT/GPLv3 terms. Concept/catalog targets resolve. The corrected delivery-report target was not yet written at this follow-up; root is preparing that file, so its existence remains a final documentation check.

Performed read-only verification of both archives. Every ZIP member was read fully through Python's CRC-validating ZIP stream; all declared payload byte counts and SHA-256 values were compared to each archive's PACKAGE-MANIFEST. No archive was mutated. Both contain exactly 39 unique members with the exact declared member set, including `NOTICE/STUDIO_SOURCES.md` and existing source/font/engine notices.

| Local archive | Bytes | Independently recomputed SHA-256 | Disposition |
| --- | ---: | --- | --- |
| `dist/yuga-native-linux-x86_64.zip` | 145,753,329 | `3ff4eb611508a261965c27b12720649b2fab3ff8cb817c2c3a2c01841304b3e9` | PASS archive/payload integrity |
| `dist/yuga-native-windows-x86_64.zip` | 153,755,118 | `4fa085156f35fe64a0a15efc32e8b405a5bf4599c92eb2fc134c10f7d7ba6335` | PASS archive/payload integrity; Windows execution UNRUN |

Both contain the same 78,219,992-byte PCK, SHA-256 `57961640ce5fd74495801e8c07a997a18da0e787e2b2e7fd8338fcb5aa7755f6`. Invoked the existing packager's `inspect_pack` against a temporary read-only extraction from each ZIP; it checked all **568 entries' stored MD5 fields** and recorded payload SHA-256. This is independent invocation/byte review of the existing inspector, not a newly authored parser or engine-execution test.

Compared the actual PCK entries to `package/embedded-studio-resources.json`: compiled `launch_briefing.gdc`, `lanka_texture_palette.gdc`, `studio_map_study.gdc`, their remaps, the map-study native scene and imported Foundry native scene all exist with matching lengths/hashes. All three packed font payloads match the export's font qualification. Compiled scripts are compared to compiled export identities; they are not incorrectly described as byte-identical GDScript source.

The packaged runtime-source identity is `121fc7b2f580b7069cd9772ec92f52627337f02f2f044369461c677e647787ed`, matching package/export embedded records. Independently hashed current `launch_shell.gd`, `launch_briefing.gd`, `lanka_texture_palette.gd`, `studio_map_study.gd`, `studio_map_study.tscn` and `studio-relay-foundry.glb`; each matches the per-file source record inside the ZIP. The new Foundry GLB hash is `468448f03984fdaadc1be3563ed0ace75b3d635cc5c546bd321c364ae55e84cf`.

`NOTICE/STUDIO_SOURCES.md` in both ZIPs is byte-identical to current source, SHA-256 `a011f144aa220167335e3957756450fd12ed875da9c6e5985d9dd20efab65cd4`. Its presence confirms the studio credits are included alongside earlier notices. It does not grant rights to excluded third-party game assets.

**Accepted:** exact local archive/payload/PCK identity, new compiled resource inclusion, packaged studio credit bytes and three font payload identities. **Separate/unrun in this audit:** personally running either package, Windows execution, remote download/publication identity, hardware performance, full-game completion and Foundry art/playability acceptance. The engineer's later actual Linux execution/captures retain their own source/artifact identity. This artifact audit does not independently certify the N4 implementation authored by this reviewer.

## Actual packaged Foundry map review

Inspected all three completed original **native** PNGs directly. These are not the separate Blender/Cycles overview. [`final-map/input-review.json`](evidence/studio/final-map/input-review.json) binds the official Linux engine, common final PCK `57961640…`, explicitly requested `gl_compatibility`, `studio_map_study.tscn`, 1280×720, XTest W/Space/O/Escape events and normal native exit 0.

| Original | SHA-256 | Actual observation |
| --- | --- | --- |
| `01-map-ground.png` | `5bf9fcb9e0c27a0a29ba83e5961776a8e5f6bd6018afd04887b27cec51b12c05` | Sun spawn, capsule scale walker, lane/tick corridor and large halls. The HUD accurately labels map study, controls, 101 collision solids and no capture/combat authority. |
| `02-map-after-input.png` | `7f77135f456df7848e45ad8581d26718c474222561b4aaabe2de4c5f037d6746` | The ground view has advanced from the spawn lettering toward the corridor after recorded input. A still at height 0 does not prove the jump arc; the scoped physics fixture owns that separate evidence. |
| `03-map-overview.png` | `107efa0d58ab71f48afc0442d5964b5a2bc7187c96b998f990c53a90e3077833` | Three lane strips, four main halls, mirrored ends, side pockets and the raised crossover are distinguishable as a coarse layout. It remains primitive blockout geometry, not finished hero-shooter map art. |

**PASS, bounded function/presentation:** native map mounts in the final package, input switches walk/overview state, the explicit exploration/no-authority scope is visible and readable, and normal Quit ends the process. The existing `art/studio-map/native-collision.json` separately records nine passing imported-physics checks at source `c46cbc96…` / asset `468448f0…`, including ramps, deck/underpass, actual capsule up/down movement, jump rise/landing and perimeter. This review read that receipt; it did not independently rerun physics or every route.

**FAIL for present ground-view art/depth readability in the inspected compatibility renderer:** broad floor/wall regions are nearly white and lose surface/depth distinction; the Sun Court surface is very bright yellow. Cover/step/material boundaries wash out. At overview scale the layout remains interpretable, but that does not repair ground-view contrast or qualify polished visuals. The HUD's dark panel remains clear. This does not identify a root cause, establish the Forward+ appearance or prove a physical-GPU defect. The next renderer/material owner should compare declared exposure/material values and matched native views before accepting map visuals. The separate Blender still must not be presented as the achieved native result.

A capture-copy integrity error was detected independently: `02-map-after-input.png` initially contained zero bytes while its receipt declared a PNG hash. The engineer restored the completed retained original atomically without rerendering or rewriting the input receipt. [`copy-integrity-recovery.json`](evidence/studio/final-map/copy-integrity-recovery.json) preserves the empty-file hash, cause and corrected identity. All three completed copied originals now match their recorded SHA-256, and this reviewer subsequently opened the restored second image. The failed copy is not silently treated as reviewed image evidence.

The actual manifest and plan now agree on **132×190 m**, six-metre crossover; all corrected plan-local links, including the now-written delivery report, resolve. The immutable ZIPs remain the same bytes accepted in the archive section above.

**Final disposition for this checkpoint:** local native archive integrity and the inspected launcher UI are accepted within scope; Foundry is an honest working exploration blockout with a visible compatibility-rendering quality defect. Complete native online game/roster, map art acceptance, every route/encounter, physical GPU performance, Windows runtime and human feel/listening/balance remain unrun or open. No new full-game production milestone is closed by the package, concept board or map study.

Launcher sizing clarification: optional briefing visibility follows the native Control's **logical canvas size**. A 960×600 physical window may still render a 1280×720 logical canvas and legitimately retain the briefing. Physical window dimensions alone do not establish the compact-layout branch. This review's enlarged/compact rendered coverage remains limited to the originals it actually opened; source/control checks retain their own scope.

Root is preparing one bounded map-lighting correction and successor package. The first candidate's failed native appearance and capture-copy recovery remain preserved above. A later image/hash follow-up can accept only the corrected scope; it does not rewrite this first result or constitute another full panel/game-production round.

## R2 correction and successor artifact acceptance

This follow-up supersedes only the first candidate's map-lighting appearance and archive identities. R1's clipped/washed-out map views, zero-byte copy finding/recovery and limited execution observations remain explicit above and in `package/r1-review.json`; its manifests are retained under `package/r1/`. No additional full panel or game-production round is claimed.

Directly opened the corrected actual native preview ground and overview PNGs. Their source receipt binds `studio_map_study.gd` SHA-256 `86d99fdf9416f2b82bb01f0b461d2a873a715d23328b61d66657adc4bf8e7af4`; map scene/GLB geometry are unchanged. The ground view now separates tan walls, teal-grey lane floor, gold spawn, pale ramp, low cover and shadows. The broad near-white clipping that failed R1 is absent in these originals. The overview also separates lane surfaces, halls, side pockets and crossover. HUD copy remains clear and explicitly says exploration prototype/no capture or combat authority.

**R2 visual disposition: PASS for blockout ground/overview depth and surface readability at the inspected 1280×720 compatibility-rendered state.** It remains flat-material primitive map art with a capsule walker. This is not final art, every-route playability, combat/navigation/authority, lighting on all devices or a human balance/feel acceptance.

The final archive run's images at `final-r2/map/01-r2-map-ground.png` and `02-r2-map-overview.png` are byte-identical to the two directly inspected corrected preview originals:

- Ground: `a30d8329dc3e492ce86695e18db8b8fa817be0b05b506536eb8d962144e7bb2a`.
- Overview: `b681cfc28ab0998b4222b226e16d2088da8543aec8e87ff9c180142331d1462d`.

Independently recomputed these hashes and compared them to [`final-r2/map/input-review.json`](evidence/studio/final-r2/map/input-review.json). That receipt binds **the final current PCK `035961b8…` and selected Linux runtime `e69af4f6…`**, records O/Escape input and native exit 0. Thus the corrected image review is bound to the successor package rather than being borrowed solely from an earlier preview export.

### Successor ZIP byte review

Repeated read-only CRC-validating ZIP streams and every declared payload SHA/size check. Re-read the extracted PCK through the existing inspector, comparing all 568 entries exactly to the current export manifest and checking every stored MD5. Also hashed **all 576 source files** listed by the packaged runtime-source manifest against current native files; every length/hash matches. Checked current NOTICE bytes, selected compiled studio/map resources and all three imported font payloads. The current embedded-resource receipt was refreshed by its owner for R2, preserving its prior R1 identity separately.

| Final local archive | Bytes / unique members | Independently verified SHA-256 |
| --- | --- | --- |
| `dist/yuga-native-linux-x86_64.zip` | 105,458,408 / 50 | `436feb85407b4035b3fac7103724fce25eac17e583bf210255bf463d1117d7df` |
| `dist/yuga-native-windows-x86_64.zip` | 153,755,332 / 39 | `c580c687ec173b41277df863202deb88430185958b030f0ca9f74dc4b991521a` |

Common PCK: 78,220,136 bytes / 568 entries, SHA-256 `035961b81f0bd13b6e19bafa5879fbba1f88206526d3542337d1af5fb4add812`. Runtime-source identity: `9a83ab6de5dbed60934de4f6288570434709af6a2c8a67405b6730592d4a2ff5`. Both archives' `NOTICE/STUDIO_SOURCES.md` matches current source byte-for-byte, SHA-256 `b1e89761d8f14cebefb7144f604fb8957dc78d0c37e82b51569cbccd84354136`.

The Linux archive now deliberately selects the 85,447,128-byte patched public-source template-debug runtime, SHA-256 `e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e`. This differs from R1's official full editor runtime and is correctly disclosed in the studio notice. Independently verified the engine payload itself plus all **eleven** bundled provenance/license evidence files against the manifest's lengths/SHA-256; the patched finished-build verification binds this binary hash, public source commit `35e80b3a8822a9df9be390814b62f44c0a9c69e8` and one pipeline-task-priority source change. Patch/before/after source evidence and Godot MIT/third-party notices are present. This closes the selected local runtime/proof identity; it does not establish a universal cold-start improvement or substitute for platform execution.

Windows retains the official runtime SHA-256 `ef90e929ba1a6a4322860285d97f40f4aa349c90329a91b0e8b55b8df0f4cb00`. Its archive/payload/PCK integrity passes; native Windows execution remains **UNRUN**.

The directly opened R2 title original `final-r2/title/01-r2-qualified-title.png` retains the accepted one-Rama/offline menu hierarchy, legible mode/action/briefing and unobscured rendered hero. That first title receipt ended in cleanup `-15`, so its image is accepted for the inspected pixels while normal title Quit was not yet accepted by that particular receipt. The engineer is completing a separate ordinary-Quit retry; this limitation must remain until its actual final observation arrives.

**Current final scope:** R2 local archive integrity, complete recorded source-byte match, selected Linux runtime/proof closure, exact studio notices/font/resource inclusion and corrected map blockout readability pass. The engineer's current package map run also records native Quit 0. Native Windows, operated online matches, complete roster/final art, physical-GPU performance, every route and human feel/listening/balance remain unrun or open. N4's author is still not its independent reviewer.

### Final R2 title Quit follow-up

The ordinary-Quit retry now closes the earlier title-cleanup gap for this exact Linux runtime/PCK. Directly opened both completed `final-r2/title-retry` originals and verified their hashes against the receipt:

- `01-title-retry-ready.png`: `5b0b716eb33da5300f3df8aef1b3039a4bb7f3a1d86406d9a8709194e08e576e`.
- `02-title-quit-focused.png`: `3e4ec00ba69f0f26b9f2f19bffb5cd2694b7aa2991deb06f378ffc4a987a0de3`.

The ready image retains readable mode/action/briefing/live-hero composition. The second visibly places the focus outline on **Quit**, distinct from the selected practice. [`title-retry/input-review.json`](evidence/studio/final-r2/title-retry/input-review.json) binds final runtime `e69af4f6…` and PCK `035961b8…`, records five Tab events, the focused-quit capture, Return and **native exit 0** after waiting for the process. This reviewer observed the originals/receipt, not a new personally operated run. The prior `-15` cleanup observation remains preserved and is not relabelled as a pass.

Final accepted checkpoint scope is now: both R2 local ZIPs and all recorded source/payload identities, selected Linux runtime/proof closure, inspected title/keyboard Quit and corrected native map blockout views/normal exit. All broader production and platform limits stated above remain unchanged.
