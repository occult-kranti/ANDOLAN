# Desktop finish S1 — W5 motion and action-feedback brief

**Audit/preparation only.** Runtime remains unchanged while the lead prepares the checkpoint. This packet selects three bounded fixes for the desktop campaign; it does not mark them implemented or visually accepted. Mobile work is deferred. No engine, import, render, test suite or commit was run for this brief.

Inspection source: `0fb96d108b1d886a4ebf84d3b5140abca3905465`, with individual working-file hashes below. Ownership is `scripts/rama_motion.gd`, `scripts/rama_hero_hud.gd`, narrow new tests and this evidence. Launch/theme belongs to W2; hero/material finish belongs to W3. Player, courtyard/world navigation, kit rules and authoritative movement/timing were read for integration context and will not be edited by this packet.

## Three selected issues

| ID / priority | Concrete finding | Evidence status | Intended bounded change |
| --- | --- | --- | --- |
| DF-M1 — initial support acquisition | G2 preserves the old provisional IK pose before safe physics, then acquires the measured support plane. That plane can differ by up to 80 mm in one update. The frozen pre-physics test and settled sole tests do not measure this transition. Title → training also changes `grounded` from the inactive-title fallback to real `is_on_floor()`. | Current source and G2's explicit limitation; the initial acquisition pop is a risk requiring a fresh transient witness, not an observed G2 visual defect. G1 title pixels show the earlier settled gap. | Measure the first final-modifier samples before changing anything. If a step exists, add a one-time pose-space acquisition treatment inside the motion owner, with one fixed measured anchor and a short bounded settle. Do not smooth/move planted anchors, shift the root/capsule or reuse rejected R4 lowering/release changes. Reject the candidate if it worsens penetration or ordinary stance. |
| DF-M2 — full-body release uses stale entry pose | `request_action()` stores `action_from_*` before windup. `release_action()` resets `action_elapsed` to zero without updating that snapshot. `evaluate_pose()` blends full-body recovery from `action_from_*` during its first 100 ms. Thus the zero-time recovery start selects the pre-windup pose rather than the outgoing pose. Measured Step is a real full-body action with 100-ms windup and 250-ms recovery. | Source-confirmed stale-snapshot path; actual-rig magnitude and visible effect are not yet measured for S1. This is distinct from G1's already-tested bow shoulder-aim entry. | After a fresh failing imported-rig witness, capture the outgoing pre-aim blend pose at an accepted full-body release and reuse the existing recovery interval. Preserve release callback, elapsed/stage/count/nock semantics and all authority timestamps. Do not alter bow-only paths or player-owned facing/translation. |
| DF-H1 — READY during another action's recovery | `_refresh_slots()` uses cooldown/reload/availability but ignores `kit.report().action_locked`, active cast phase and pending buffered input. The kit rejects another immediate action while locked. The 80-ms slot refresh can also delay a semantic transition even though vitals update each rendered frame. | Historical actual package witness plus current unchanged logic: I3 frame 11 has Piercing Dawn age 0.8 s, phase `recovery`, `action_locked=true`, while E/C/X show `READY`. This is not a fresh S1 execution. | Read the current authoritative active cast and buffer state; distinguish the active windup/recovery, other busy slots and a genuinely queued action. Refresh semantic changes on the next HUD process frame; keep throttling only numerical cooldown text if useful. Preserve ammo, cooldown and current pause/death/outcome precedence. No new timer, input behavior, authority or theme owner. |

Suggested implementation order after the checkpoint: first prove DF-M2 and make its small release-snapshot correction; then implement DF-H1; use the first-visible-frame capture to decide whether DF-M1 warrants a correction. Do not change startup contact solely to make a source hypothesis look complete. Each attempt gets its own baseline/candidate bytes and report; a rejected result stays rejected.

## Current transition and ownership contracts

`player._physics_process()` intentionally updates motion for an inactive title actor. `_update_rama_motion()` returns when the explicit `presentation_suspended` flag is set, then passes actual motion inputs, `floor_y=player.global_position.y` and `grounded=is_on_floor() or not active`. Courtyard `start_training()` switches camera, activates the living player and resumes practice; `return_to_menu()` resets practice and returns to the title camera. Confluence overview sets explicit presentation suspension. A generic `active=false` test must not replace these distinct title and overview behaviors.

The G2 controller samples a nearby almost-flat plane only in safe physics, then fixes the anchor. Its settled actual-title numerical soles were about +0.572 mm versus G1's +50.571 mm. The initial-pose test only compared the pose *before* physics and repeated evaluation without an update; it did not compare before/after the first safe query. These are retained G2 results, not new S1 passes. The current capture helper's title/training preroll also skips first acquisition, so two settled stills cannot close DF-M1.

The kit owns the 20-Hz action clock and public release/cancel events. Runtime supplies `request_action()` at begin and `release_action()` at the matching authority event. Measured Step's movement receiver still owns its 0.22-s movement. The proposed DF-M2 pose handoff cannot delay the release, change movement, extend commitment or manufacture a second release. Bow grip/string/muzzle and complete lower-body motion need checking even if a pose-origin metric improves.

For DF-H1, distinguish “cooldown available” from “can act now.” Read `active_cast_id` and the corresponding cast record; do not select an arbitrary lingering projectile/ward from `casts`. A released Guardian field can remain active after the hero is free to act. The action buffer accepts only one deliberate Piercing/Volley edge near actual recovery; show `QUEUED` only for its real matching-generation pending record, never because the HUD predicts that a press might be accepted. A label change must not dispatch, cancel or extend that pending input.

## New checks to implement after checkpoint

These are proposed new fixtures, not reruns counted as new round completions.

| Issue | New adversarial witness | Required invariant / rejection condition |
| --- | --- | --- |
| DF-M1 | Observe the actual imported rig from the first modifier callback, across first physics admission and the first 12–20 physics/draw samples. Exercise cold title, immediate start before settle, settled title → training, reset → title and pause exactly between provisional and admitted support. | Same callback body/rig/sole/ground data; all selected sole vertices and affected body joints, not only foot targets. Record transient position/velocity change and settled result. No root/capsule movement by the motion owner; fixed anchor unchanged after acquisition; ordinary support coverage and penetration must not regress. |
| DF-M1 | First admission hits the real plane, misses, rejects a slope or occurs after reset/flight. Evaluate twice without updating between each phase. | No new draw-clock advancement, unsafe physics query, perpetual admission retry or moving anchor. Add temporal observations to the existing boundary conditions; merely repeating G2's steady assertions is insufficient. |
| DF-M2 | Actual imported Measured Step: sample immediately before public release, call the matching release once, sample at the same presentation time, then continue through recovery at 30/60/120 Hz. Include moving/idle entry, interrupted windup and a reset just before release. | Demonstrate the stale-pose boundary first. Candidate removes the targeted same-time rewind without worse subsequent joint/skin/socket steps. Compare kit/movement/event receipts exactly. Duplicate or mismatched releases still fail and cannot change the pose. |
| DF-M2 | Freeze/overview across release scheduling; release/recovery then fresh cast; immediate repeated pose evaluation; full-body hit/respawn presentation as guards where callers actually use them. | No additional clock, doubled aim, stale snapshot after reset, or corpse revival. Existing bow entry/cancel behavior is a regression guard, not a newly claimed G1 achievement. |
| DF-H1 | Real kit windup → release → recovery → unlock, while untouched abilities have zero cooldown; sample HUD on the next rendered/process frame and immediately below the old 80-ms interval. | Active slot and other busy slots describe actual state. No false READY during an immediate-input lock. Authoritative cooldown/ammo remain visible and exact under the chosen wording. State text must fit the existing desktop card layout. |
| DF-H1 | True near-recovery queue, invalid/expired queue, cancel, generation reset, paused overview, defeat/respawn, terminal outcome, and runtime detach/disposal while HUD remains alive. | QUEUED only for a valid pending intent; correct availability precedence; stale action feedback clears. HUD refresh cannot advance kit, army, motion or buffer. No callbacks on freed owners or added engine errors. |

Use one lightweight CPU lane only after the lead releases it, single engine thread and LP/OMP/BLAS=1. No broad overlapping suite or asset reimport. Keep the current controller as the differential baseline and preserve failed candidate data. Source and imported-asset hashes must match each report. Existing regression suites may be run where justified, with their role stated separately from the new witness.

## Concrete continuous-capture request

W6 owns the capture implementation and root owns scheduling. Do not start a renderer for this brief. Use the actual final-modifier observer and a matched source/camera/lighting/LOD freeze, including all combined finish changes. Current G1/G2 candidates need their own actual proof; an old R4 frame cannot be relabelled as a candidate frame.

1. **Startup/support take:** record from the first drawable courtyard hero, before the usual title preroll; keep approximately the first 0.6 s, then use the real Bow training action and record its first 0.6 s. Include the actual title camera and gameplay transition. If the camera switch obscures contact, add one explicitly controlled fixed-camera diagnostic with the same actor/physics chronology; label it separately from native navigation. Preserve frames before and after the first safe query, not just the final supported pose.
2. **Measured Step release take:** in settled live practice, use the real E binding and retain windup, authority release, movement and recovery. Repeat with ordinary movement input if the first take is clean. Observe full-body framing, bow/string/hand, lower limbs, actor translation and the exact release event. At 30-Hz capture, pair every drawn sample with the underlying 60-Hz physics event record; do not call a sampled frame delta a mathematical C0 discontinuity.
3. **HUD/action take:** real Piercing Dawn → one other action attempt during windup → near-recovery deliberate Volley queue → dispatch. Include one cancel and overview hold/resume with the actual pending-state policy. Retain the HUD text/state, kit active cast/phase, buffer generation/pending record, release/cancel counts and motion state. The existing 60-frame G1 cancel/retrigger helper may supply useful controls, but it does not automatically cover Measured Step or initial support.

All takes need final modified poses and skinned soles recorded during `modification_processed`, consistent physics/draw counters, active LOD, world-space targets and actual floor ray. Record `idle_support_ready`, candidate acquisition state, pause/active/presentation-suspended flags and exact action event ages. No time monkeypatch, hidden delayed release, movement retune or second skeleton writer. Actual continuous normal-speed review is mandatory; physical GPU performance and human input/feel remain open.

## Prior originals actually opened for this audit

Six original PNGs were opened. These are historical observations; no full MP4 playback or new image was produced. The two temporary I3 images were verified byte-for-byte against their repository archives before linking below.

| Original | What it supports | SHA-256 |
| --- | --- | --- |
| [G1 title day](../../graphics-six/G1/native/01-title-day.png) | Apparent settled sole/floor separation before G2; cannot establish startup pop | `2be1303891e9feb231d7903bd3f86c6811a425d7e6c1c281b026046c63ba73a4` |
| [G1 world day](../../graphics-six/G1/native/03-world-day.png) | Existing compact HUD composition and hero framing at rest; not action-flow acceptance | `2cdc03c98387e01e506c0239a8a491ca6beee45fcb4de70c4472415955e922f8` |
| [R4 frame 149](../../visual-rounds/round4/role06/originals/frame-149.png) | Pre-cast frame of the historical motion baseline | `81ddbe990a0bc22beab101784da400bd39fc8b04cd867144f82b82ed9b81339d` |
| [R4 frame 150](../../visual-rounds/round4/role06/originals/frame-150.png) | Adjacent historical cast-facing adjustment; player-owned yaw is outside this packet | `db7733cc6dffe6442a391f2b4ffaf0b0c4040c3acc2ef8867fe08d13d8b63690` |
| [I3 overview hold](../../ui-campaign/I3/role03/native-r1/09-package-overview-unreleased-a.png) | Paused availability and old packaged hold composition | `6573a8ad763b7c0c646144e289f12b3b3d8632befd9f4502ead85c03a0016627` |
| [I3 resumed release](../../ui-campaign/I3/role03/native-r1/11-package-overview-resumed-release.png) | READY labels during an actual action lock; [paired state](../../ui-campaign/I3/role03/native-r1/11-package-overview-resumed-release.json) records age 0.8 s, recovery, locked=true, release_count=1 | `4c634275ae7e580631ed0c13acfeb32c8a30a353825243120b144ee4e897c511` |

Read prior [G1 motion](../../graphics-six/G1/motion.md), [G2 motion](../../graphics-six/G2/motion.md) and [R4 independent tape review](../../visual-rounds/round4/role15/REVIEW.md). Their counts and dispositions remain historical. In particular, the 210-frame R4 source predates G1/G2 and the later overview correction. The old no-release cancel result, zero fixed-anchor drift and visible stop/landing failures remain useful controls, not fresh S1 acceptance.

## Current source pins and handoff

| Path, relative to `games/yuga-native/` | SHA-256 |
| --- | --- |
| `scripts/rama_motion.gd` | `35a9e58e6c720c67cd6e77fb812900bc05dec9d2fbd255b7bd8aa40b39e20fb3` |
| `scripts/rama_hero_hud.gd` | `4ea25f796ed3c3ac5a1ca6d25edd177d06490632e3c43039912929a744c3f064` |
| `scripts/player.gd` | `54beb1c88df226983edf8bf4609b989731c0915103e590b97d303f77f845cc86` |
| `scripts/courtyard.gd` | `197a2349cebdf26d195bcec64c9380f74c76537970def2ea9bea3193086b5a30` |
| `scripts/confluence_world.gd` | `20f809f9ead1d98f3b018c1f38d699d072fa81f3439d44c3369a5b4d249e7450` |
| `scripts/rama_hero_runtime.gd` | `7ff170bbb9f5b5e20dabd84a3116e38982deb1decfa200666aeed1f37c15627a` |
| `scripts/rama_ability_kit.gd` | `ed8ac617c003ee1307c2cfff5a093ebbc092cc40b60b1c4b2d751a0a165323cc` |
| `scripts/rama_action_buffer.gd` | `f8c3e3c246b76ff7454063f0d5f7fd573c90ebdf383fb7aad0606c14e9ca2ec4` |
| `assets/animations/rama_hero_motion.tres` | `1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8` |

The only file written by this audit is `docs/evidence/desktop-finish/S1/motion-brief.md`. Checks performed were read-only source inspection, original-image opening, JSON-state reading and image/source SHA comparison. No new runtime test result or fix is claimed. Lead checkpoint/release is the next dependency; W5 then owns the fresh counterexample and bounded implementation, W6 the independent challenge and source-bound continuous capture. Material richness, original full production art, ordinary stop/landing contact, player-owned facing, physical GPU speed and human feel remain separate open gates.
