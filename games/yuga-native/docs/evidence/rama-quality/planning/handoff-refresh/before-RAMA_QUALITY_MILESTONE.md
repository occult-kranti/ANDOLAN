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

The current player integrates per-instance PBR calibration, bounded secondary
motion and authored facial performance when the imported art provides their
required data. The runtime integrates a short Q/X recovery buffer and fifteen
original pooled action cues from actual combat/vitals receipts. Face and LOD
promotion require their own actual-art review; a failed configure cannot count
as an implemented visual feature.

Combined input/audio checks currently pass **45/45**, alongside existing
integration **138/138**, combat **85/85**, motion **39/39** and saved bindings
**44/44**. Exact tested sources and the narrower claims live in
[the combined report](evidence/rama-quality/gamefeel/combined-r1/REVIEW.md).
These runs do not establish actual OS responsiveness, listening quality,
consumer-GPU frame rates or final visual acceptance.

## File map for the next worker

| Work | Source / entry point | Important boundary |
| --- | --- | --- |
| Hair, costume and semantic cloth masks | `art/hero-rama-quality/` | Q3 is a reviewed, limited art input; use its exact frozen source before a dependent export. |
| Native eyelid authoring | `art/hero-rama-face/` | Keep rejected overlays and failed source-pose calibrations separate. Review the entire eye aperture, corners and adjacent frames. |
| PBR and secondary response | `scripts/rama_surface_materials.gd`, `scripts/rama_secondary_motion.gd`, `shaders/rama_secondary_cloth.gdshader` | Six material names and four secondary names are disjoint. Preserve original channels and masks. |
| Facial playback | `scripts/rama_facial_performance.gd` | One small native face mesh; no eye scaling or second skeleton writer. |
| Input and original audio | `scripts/rama_action_buffer.gd`, `scripts/rama_action_audio.gd`, `assets/audio/rama-quality/` | Presentation follows actual accepted kit/vitals events; queueing is not a cast. |
| Combat presentation | `scripts/rama_ability_effects.gd`, `shaders/rama_ribbon.gdshader` | Existing authority, contact geometry, field expiry and fixed budgets remain the contract. |
| Rig-preserving LODs | `art/hero-rama-lod/`, `scripts/rama_visual_lod.gd` | Generate after final art freezes; bind all levels to one existing 164-bone rig. |
| World and screens | `scripts/production_lighting.gd`, `scripts/world_lighting.gd`, `scripts/courtyard.gd` | Actual lighting/material A/B and package input are separate from logic checks. |
| Original arrival architecture | `art/quality-arrival-court/` | Source design alone does not establish an exported, placed or collidable district. |
| Remote pose and practice intent | `scripts/rama_remote_replica.gd`, `scripts/rama_practice_brain.gd` | Foundations only: neither creates native online matches or a second native hero authority. |
| Build identity and license chain | `NOTICE/RAMA-HERO-PROVENANCE.json`, `tools/package-native.py` | Preserve exact R7 ancestry, terminal source and CC0 pose-data dependencies when promoting later art. |

## Resume in order

1. Check branch/status and current owners. Preserve the released evidence and
   meaningful rejected candidates; use fresh scratch output directories.
2. Close the named actual-art blocker before handing the final geometry to LOD.
   Keep one rig, one motion writer and one native facial mesh. Configure material
   components after all accepted LOD meshes are attached.
3. Freeze source, import and asset identities. Run affected component and actual
   world checks; refresh native content pins only after controller/runtime freeze.
4. Capture matched actual scenes with `tools/run-rama-lookdev.py`. Review
   continuous gameplay and actual package input independently. Record visible
   defects even when numerical checks pass.
5. Advance P1 only after the required art, motion, arena, audio, human review and
   declared hardware evidence exists. P2 then connects the same slice to native
   authority. Do not multiply the roster to bypass the quality gate.

No full-game completion percentage is assigned. Native online integration,
fourteen production heroes, full-map finishing, human balance/listening,
Windows execution and physical-GPU profiling remain open. The dated planning
ranges and conditions are in the quality target; specialist agent count is not
a measured production rate.
