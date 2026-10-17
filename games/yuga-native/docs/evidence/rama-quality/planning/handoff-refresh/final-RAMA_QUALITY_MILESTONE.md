# Rama quality production: fifteen-role handoff

This production pass continues the original YUGA native game on
`game/yuga-native-production`, starting at
`1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`. It does not replace the
[published offline preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-rama-hero-2026-10-17)
or claim commercial-game visual parity.

Read the [quality target and P0–P6 delivery gates](DEADLOCK_QUALITY_TARGET.md),
[fifteen specialist work packets](PRODUCTION_SQUADS.md), and
[independent acceptance record](RAMA_QUALITY_ACCEPTANCE.md). They extend the
[full-game production roadmap](FULL_GAME_PRODUCTION_ROADMAP.md); the machine
ledger remains [ROADMAP_BACKLOG.json](ROADMAP_BACKLOG.json).

## Current integration

All fifteen specialist roles received bounded work in rotating waves. This
environment allows six workers plus the lead at once. Child review agents use
the same capacity and receive exclusive files. Their results are component
deliveries, not fifteen completed game systems.

The final repaired native face and high/mid/far hero assets are staged at
`assets/heroes/rama-hero{,-mid,-far}.glb`. The high asset is `de61dc4c…`; the
three levels share one existing **164-bone rig** and one motion writer. The
player configures per-instance PBR calibration, bounded secondary motion and
native facial performance after attaching the LOD meshes. The runtime integrates
a short Q/X recovery buffer and fifteen original pooled action cues from actual
combat/vitals receipts. Native remote-pose and practice-brain components remain
separate from an integrated online or bot match.

| Evidence | Latest bounded result |
| --- | --- |
| [Actual frozen-world integration](evidence/rama-quality/qa/positive-r4/summary.json) | **31/31**: real staged assets, one rig, three presentation controllers, actual LOD route, lifecycle and 100 resets. |
| [Full quality runner R3](evidence/rama-quality/integration/full-suite-r3/summary.json) | **All 16 suites pass: 777 assertions plus 15 deterministic PCM files.** Runtime and checked-source hashes are unchanged; the full logs contain zero WARNING, ERROR or SCRIPT ERROR diagnostics. |
| R3 included component suites | Audio **115**, native face **41**, lighting **146**, input-buffer offline integration **47**. These counts are part of 777, not additional assertions. |
| [Final source/provenance checks](evidence/rama-quality/planning/final-native-contracts/README.md) | **42/42** source pins, **242/242** pure contracts, **118/118** provenance counterexamples and **23** actual canonical authoring records. Native offline content revision remains **4**; other profiles/wire versions are unchanged. |
| [Matched lookdev R2](evidence/rama-quality/lookdev/capture-r2/lookdev-capture.json) | Twelve PNGs/six pairs captured; the earlier floor bands are absent in the sampled stills. The preview-based missing-label finding is **RETRACTED**: independent decoded-pixel checks confirm the text is present and all eight original R1/R2 label regions are byte-identical (630 dark text pixels). No product fault is established by the retracted finding; its preview/perception cause is unknown. Actual input and final art gates remain open. |
| [Five-action gameplay capture R1](evidence/rama-quality/gameplay/capture-r1/capture-run.json) | Complete: **363 frames and 25 stills**, all five actions reach normal expiry, source/import pins unchanged and no engine warning/error diagnostics. Encoded movie decoded successfully. It is silent, simulated 30 fps, script-invoked and contains five deliberate reset cuts; independent release/expiry review is underway. Sampled stills support bounded VFX/readability improvement; face/contact/secondary are too small or occluded for acceptance, and three lifecycle stills do not establish continuous death/respawn appearance. |
| [Native LOD capture R1](evidence/rama-quality/lod/native-capture-r1/capture-run.json) | Complete: **six pairs/twelve PNGs plus thirty frozen-pose camera frames** (42 PNGs total). Source/import/state validation passes with zero engine warning/error diagnostics; exact sources, reports and a camera movie are archived. Independent pair/frame review is underway. Frozen-pose footage does not establish animated deformation quality or physical-GPU performance. |

[Full-run R2](evidence/rama-quality/integration/full-suite-r2/summary.json)'s
**775** passing assertions and its **two shutdown warnings** are
preserved alongside R3. R3 adds two teardown cases; it does not erase that prior
finding. Older combined-input/audio and focused reports remain historical
source-bound evidence, rather than the current full-run result. Headless checks
do not establish actual OS responsiveness, device/listening quality, consumer-GPU
frame rates, rendered label visibility or final art acceptance.

The [decoded title-label audit](evidence/rama-quality/lookdev/title-label-diagnosis/summary.json)
records the pixel evidence that supersedes the preview-based finding. The
[independent dated correction](evidence/rama-quality/qa/lookdev-r2-review/label-correction-2026-10-17.json)
confirms the retraction; original review JSONs remain preserved with superseded
markers. Other art limitations remain open.

The repair from reviewed `1fdb01cc…` to `de61dc4c…` fixed exactly three zero
TANGENT records. **7,797 nonorthogonal tangent records remain a separate
material-frame rebake/review packet.** Do not relabel the zero-tangent patch as
completion of that broader work. Preserve the reviewed geometry, skin, facial
morphs and original authoring chain when producing the next candidate.

## File map for the next worker

| Work | Source / entry point | Important boundary |
| --- | --- | --- |
| Hair, costume and semantic cloth masks | `art/hero-rama-quality/` | Q3 is a reviewed, limited art input; use its exact frozen source before a dependent export. |
| Native eyelid authoring | `art/hero-rama-face/` | Final repaired native face is staged. Preserve rejected overlays, the reviewed pre-repair asset and the exact CC0 pose inputs; review the complete aperture and adjacent frames after changes. |
| PBR and secondary response | `scripts/rama_surface_materials.gd`, `scripts/rama_secondary_motion.gd`, `shaders/rama_secondary_cloth.gdshader` | Six material names and four secondary names are disjoint. Preserve original channels and masks. |
| Facial playback | `scripts/rama_facial_performance.gd` | Native orbital-partition morphs on the existing skinned body and one skeleton writer; preserve mid-blink death/reset behavior. |
| Input and original audio | `scripts/rama_action_buffer.gd`, `scripts/rama_action_audio.gd`, `assets/audio/rama-quality/` | Presentation follows actual accepted kit/vitals events; queueing is not a cast. |
| Combat presentation | `scripts/rama_ability_effects.gd`, `shaders/rama_ribbon.gdshader` | Existing authority, contact geometry, field expiry and fixed budgets remain the contract. |
| Rig-preserving LODs | `art/hero-rama-lod/`, `scripts/rama_visual_lod.gd`, `scripts/rama_lod_binding.gd` | High/mid/far assets are staged and bound to one 164-bone rig. Any accepted art revision requires dependent LOD regeneration, validation and actual switching review. |
| World and screens | `scripts/production_lighting.gd`, `scripts/world_lighting.gd`, `scripts/courtyard.gd` | Actual lighting/material A/B and package input are separate from logic checks. |
| Original arrival architecture | `art/quality-arrival-court/` | Source design alone does not establish an exported, placed or collidable district. |
| Remote pose and practice intent | `scripts/rama_remote_replica.gd`, `scripts/rama_practice_brain.gd` | Foundations only: neither creates native online matches or a second native hero authority. |
| Build identity and license chain | `NOTICE/RAMA-HERO-PROVENANCE.json`, `tools/package-native.py` | Preserve exact R7 ancestry, terminal source and CC0 pose-data dependencies when promoting later art. |

## Resume in order

1. Read [repository START_HERE](../../../docs/START_HERE.md), this handoff and the
   latest acceptance records; check
   branch/status and live file owners before editing. Preserve the released
   preview, source-pinned reports and meaningful rejected candidates. Use fresh
   scratch outputs and the agreed heavy import/export/render slot.
2. Start with the next-five queue below. The face and LODs are already staged;
   do not restart the obsolete R7-to-face promotion task. Any new art candidate
   must preserve one rig/motion writer, native morph ownership and semantic
   material/cloth masks, then pass independent actual-output review.
3. Compare the current source/asset/import hashes with the report being used.
   A code or art change makes the relevant old evidence historical. Root owns
   new runtime manifests, NOTICE promotion and final content-pin refresh after
   source freeze; never repin a source merely to silence a failing gate.
4. Use `tools/run-quality-checks.py --list` to inspect the sixteen-suite catalog.
   After the normal environment setup/import, run the whole catalog with the
   configured Godot 4.6.3 and a NumPy-capable Python, a fresh `--output` directory
   and no `--suite` filter. The runner creates separate temporary XDG directories
   and retains reports/full logs; it does not import, render or validate online
   play. Review all logs and source-before/after guards with the result.
5. Use the existing matched lookdev, gameplay and LOD capture harnesses for
   actual images and sequences. Record visible defects even when numerical
   cases pass. Advance P1 only after the declared art/motion/arena/audio,
   package input, human and hardware evidence exists. P2 connects this same
   quality slice to native authority before broader roster production.

## Next five prioritized packets

These are future bounded work orders, not completed features. Root assigns
exclusive files and may overlap independent work within the six-worker limit.

| Priority | Named owner and supporting roles | Concrete result and dependency |
| --- | --- | --- |
| 1. Material-frame authoring and matched art review | **11 Performance/asset interchange**; 04 face authoring, 02 materials, 14 independent QA | Diagnose and rebake the 7,797 nonorthogonal tangent frames from the exact frozen source, preserving reviewed geometry/skin/morphs. Validate original and candidate under the same materials/cameras, regenerate dependent LODs after acceptance and retain the exact authoring/provenance chain. The three-zero repair is already complete. |
| 2. Actual package screen and input journey | **12 UI/accessibility**; 06 capture/lookdev, 14 QA | Review real keyboard/mouse/remap/focus behavior through title/settings/help/start flows at declared screen sizes. The retracted preview-based label concern requires no product fix; keep the decoded-pixel correction with the historical report. Depends on an exact preview package from root/15 after the relevant source freeze; final qualification is packet 4. |
| 3. Continuous hero, five-action and LOD quality | **03 Animation/secondary**; 05 VFX, 11 LOD, 13 audio, 14 QA | Independently review completed gameplay/LOD sequences, then correct specific hair/cloth/contact/face, action timing, effects/counter or LOD-pop defects. Repeat current-source day/night and crowded-action evidence. Depends on accepted candidate from 1 and completed captures; listening remains an actual listener task. |
| 4. Exact package and declared hardware qualification | **15 Build/production**; 12 input/accessibility, 13 listening, 11 performance, 14 QA | Build and run the exact accepted package; verify keyboard/mouse/remaps, focus, pause/reset, audio priorities and installation on declared platforms. Profile a stated physical-GPU/display matrix with normal and dense encounters. Depends on 1–3 and final hashes; software Vulkan is insufficient for a consumer FPS claim. |
| 5. Same-quality native authority slice | **09 Network/services**; 08 combat, 10 practice intent, 15 build/security, 14 QA | Connect the accepted same hero/map to real authority and two rendered native clients. Show movement, actions/hits, death/respawn, reconnect/version rejection and results without synthetic action authority. Depends on the frozen map/entity/rules contract and accepted slice from 1–4; a pose adapter alone does not close it. |

No full-game completion percentage is assigned. Native online integration,
fourteen production heroes, full-map finishing, human balance/listening,
Windows execution and physical-GPU profiling remain open. The dated planning
ranges and conditions are in the quality target; specialist agent count is not
a measured production rate.
