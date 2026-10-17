# Native production task board

The current goal is original native YUGA art and systems that can be inspected
and improved toward the requested visual target. The current courtyard is a
render/animation test scene, not completion of the competitive multiplayer game.

## Four-round work contract

1. **Inspect:** identify the exact source/asset, existing defect and intended
   change. Record evidence and a bounded subgoal.
2. **Build:** make the smallest useful artifact or correction. Keep code and
   model licenses separate; retain original source hashes.
3. **Verify:** import, render or run relevant regressions on a frozen revision.
   A failed frame is a finding, not a completed visual gate.
4. **Report and integrate:** state what passed, what remains unresolved and the
   next dependency. Root reviews the handoff and publishes the tested revision.

Reports occur at subgoals, not after arbitrary waiting periods. If a render
exposes a correctness defect, return to Build and preserve the failed attempt.
Completed studies are not repeated to inflate a round count. Every run ends
with a concrete report; no unattended perpetual agent loop is implied.

## Current ownership and dependencies

| Squad / lead | Owned work | Subgoal / next dependency |
| --- | --- | --- |
| Research: mythology/source lead + bounded REA/game scouts | `docs/research/` source indexes and character reuse audit | Pin actual reconstructed-engine loaders and model licenses; report a usable reference asset and excluded candidates |
| Reference character: native engine lead | `art/reference-models/`, isolated import and character comparison | Download a clearly reusable rigged model, inspect/import it and map compatible skeleton concepts; preserve YUGA's active hero |
| Hero artist + art director | `art/production/`, production Rama and visual review | Final v4 idle/run/defeat review confirms restored fingers and closed calf openings; sculpt/cloth/action quality remains a separate larger milestone |
| Environment artists | Courtyard generator/model, lighting and water shader | Inspect final dusk/night native frames; preserve walkable routes and camera clearance |
| Physics + native QA | Projectile lifetime correction and `tests/` | Re-run final production asset checks, retain failure history and distinguish numerical checks from visual acceptance |
| Root integration | Runtime integration, source freeze, captures, packaging, CI and branch publication | Inspect final scene and hero evidence; export exact source, verify packages and publish an honestly scoped preview |

Workers may create a narrowly scoped child when it saves time. The session's
seven-worker limit is a ceiling, not a goal; only one heavy actual renderer
runs at a time. Shared files have one owner. A model or shader change invalidates
the corresponding old render/package proof, not unrelated source research.

## Round-four handoffs

- [Hero artist](../art/production/RAMA_REVIEW_ROUNDS.md): four recorded revisions;
  introduced hand/calf defects closed in inspected v4 frames, broader art gaps open.
- [Character import squad](research/REFERENCE_CHARACTER_IMPORT.md): two fresh
  isolated imports reproduce the corrected names and finite samples; 21 bone-map
  candidates remain unapplied. Next: one locomotion clip and one aim pose with
  rest-axis compensation and actual contact/motion review.
- [Research squad](research/CHARACTER_REUSE_AUDIT.md): five reconstructed/open-game
  character pipelines compared; a licensed reference selected and independently
  cross-checked, with source/asset licenses and conversion gaps recorded.
- [Physics/QA squad](../tests/README.md): 18 native and seven projectile checks
  pass; failed attempts and the limits of structural tests remain recorded.
- [Integration](PRODUCTION_REVIEW.md): final actual-render evidence, clean-source
  portable packages and successful CI; Windows execution and physical-GPU
  performance remain separate future gates.

## Wider-game gates

The [native roadmap](NATIVE_PRODUCTION_ROADMAP.md) tracks one production-quality
hero/lane, protocol-2 native multiplayer, three-lane objectives/economy, roster
expansion, operated services and platform release. Each milestone requires
its own testable result. Source availability, a parser, a fork count or a
successful asset import cannot establish finished-game or visual parity.
