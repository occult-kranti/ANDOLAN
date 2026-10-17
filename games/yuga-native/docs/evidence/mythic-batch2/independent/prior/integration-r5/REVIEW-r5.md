# Independent MYTH08/09/10 integration review

2026-10-17. Native YUGA working tree over `eedfd1f94181cddfad293e3e95f126b96c72baed`.
Owner changed only `tests/mythic_integration_cases.gd`, scratch probes and this approved
evidence archive. Implementation fixes belong to the session, FX and root glue owners.

**Final result: 97/97 real-world integration checks pass; 170/170 retained independent
contract probes pass against contract revision 2.** Final integration is r5. Prior r4
refreshed the FX reset-replay guard; r5 adds the packaged-window empty-cast notice
regression and lower-left HUD geometry on root’s corrected world source. All 29
integration source pins match the checkout at final review.

## Three rounds and one observed correction

1. **Contract challenge.** Read the actual MYTH08 plan, receiver/army code, source rules
   and UI/FX contracts. Challenge decorative-versus-authoritative dimensions, combined
   receipts at 72 receivers, current shield/summon attachment positions, independent
   preparation clocks, reset reentrancy and successful reconfiguration ownership.
2. **Real execution and correction.** Instantiate the actual confluence world, use its
   real session, troops, FX, panel and audio, and retain failing probes/reports. First
   world run was 66/68: sector warning vertices exceeded their authoritative shapes.
   Expanded r2 passed 81/81 after corrections; r3 added audio and options for 91/91.
3. **Frozen verification.** Fresh r4 passes 91/91 on final FX `61fb1442…`. Sources are
   hashed before and after the run, including the test, audio manifest and all 16 WAVs.
   Re-run the retained independent contract probes without changing their test
   semantics: 43 type/tamper cases plus 127 replay/descriptor cases pass.
4. **Packaged-window correction.** Root observed a zero-receipt cast still showing
   “Preparing · aim locked” after release and a centre-bottom status card crossing
   the hero. Root corrected the notice transitions and moved the card. Fresh r5
   retains all prior checks and adds six real event/layout checks: 97/97 pass. The
   earlier r4 report/log/review remain under `prior/integration-r4/`.

## Defects and accepted closure

| Finding | Evidence | Correction and verification |
|---|---|---|
| Reset during a `defeated` callback attempted to free a locked emitter, then emitted an old damage receipt as cast 0 in the new epoch | `probes/reentrant-reset-probe.log.txt` | Owner defers unsafe freeing and rechecks epoch/cast after receiver mutation. r2 probe and final integrated reset restore 30 healthy troops, emit no old receipt into the new epoch, and reject delayed old presentation. |
| Finite aim `(1e30,0,1e30)` overflowed squared length and normalized to zero, yet was accepted | `probes/huge-forward-probe.log.txt` | Owner rejects nonfinite squared magnitude before event/cooldown mutation. Repaired probe and final malformed-input test pass. |
| Successful reconfiguration replaced the army before retiring previous owned effects | Read-only checkpoint review; `probes/reconfigure-probe.log.txt` is the subsequent passing proof | Owner clears old statuses/temporary units before replacement. Final real-world test preserves state on invalid configure and clears previous shield/subscriptions on valid configure. No claim of a retained failing execution for this finding. |
| Duryodhana/Meghnad warnings had 5/4 vertices outside the authoritative sector | `rejected/integration-r1/report.json` | Artist corrected stroke edges. Final strict world-space vertex tests pass, including low-effects visibility; source geometry stays authoritative. |
| Cosmetic player countdown could independently authorize actions before the army-clock release | Code review, followed by an adversarial clock-order acceptance test | Root added a preparation latch cleared by release/cancel/reset. Final actual grounded cast remains movement/fire/traversal locked after 1.2 seconds of player-only advancement while authority stays in windup, then releases on the actual authority event. No fabricated pre-fix failing execution. |
| Zero-receipt cast retained preparation text after release; centre-bottom HUD occupied the hero area | Root’s actual packaged-window review; new final real-event and layout checks | A real grounded world cast with no eligible receivers must update preparation → release → end → reset through the actual HUD timer. Lower-left card fits both logical sizes without visible HUD overlaps or crossing a declared central layout reserve. This numerical reserve is not a measured hero silhouette. |
| First short fixed-FPS exit logged an ObjectDB leak warning | `rejected/integration-r1/run.log.txt` | After freeing the real scene, the test allows 100 ms for the existing audio thread to retire playback and then samples more frames. Final verbose runs have no errors/warnings and node count returns from 1 to 1. This is test teardown timing, not a claimed runtime resource rewrite. |

The deferred reset may advance the epoch twice: once for immediate invalidation and
once for completed reset. Tests require monotonic separation and absence of stale
receipts, rather than assuming exactly +1.

## What the 97 checks establish

- Every one of the fourteen invocation IDs begins through the **real world-owned
  session**, routes into actual FX/audio, and applies native troop damage, capped
  healing, shield absorption, slow status or two actual temporary units. These are
  invocations through Rama, not fourteen finished playable models.
- Tests isolate actual commander receivers in documented clear ground, suppress
  unrelated ordinary movement/attacks, and manually advance the real army at 20 Hz.
  Summon units are real normal receiver nodes; their role, attack override, expiry,
  zero core damage and absence of expiry rewards are checked.
- Receipts match actual before/after health/shield changes; one combined receipt per
  affected unit preserves all 72 damage-plus-slow mutations. The six-second zone
  produces the exact clipped total and history remains bounded at 64 events.
- Shield visuals follow accepted live unit positions and retire on depletion;
  duplicate/old-epoch presentation cannot mutate gameplay. Warning vertex tests use
  actual mesh coordinates transformed into world space and authoritative geometry.
- Shared twelve-second cooldown survives selection and cancellation. Real panel
  preview does not select; choose routes to the session. Real option signals reach FX.
  World pause, overview and focus loss freeze session/presentation and reject casts.
- A separate test exercises the actual grounded `cast_invocation()` world entry,
  player preparation latch, delayed authority clock, action release and rejection
  preserving animation. The fourteen payload fixtures use the real session API;
  they do not pretend to be fourteen physical keyboard-input sessions.
- Original audio is admitted by actual begin/release events, remains bounded to
  three players/sixteen streams, rejects duplicate/malformed receipts, obeys world
  volume zero and pause, retires prior cues on cancel, and clears on world reset.
- An actual grounded, zero-hit world cast announces preparation, release with
  movement restored, completion and reset readiness through the periodic HUD path.
  The exact 330 × 100 card lies at (20,394) for a 960 × 600 logical viewport and
  (20,514) at 1280 × 720. Both labels fit and visible HUD cards do not overlap. A
  central lower 200-pixel layout reserve is clear; OS scaling and the actual hero
  silhouette remain visual-review concerns.
- Reentrant reset, invalid/successful reconfigure, old epochs, 24 repeated world
  resets and full scene disposal preserve callbacks/node bounds. Final node count is
  exactly the initial single SceneTree root node.

Existing ordinary army, siege and relay suites were run separately by their owners;
their results are not relabelled as this reviewer's executions.

## Commands and exact pins

No imports or rendering were started by this reviewer.

The audio owner subsequently changed only the sixteen invocation import settings
to preserve PCM16 instead of default QOA compression. This report pins the WAVs and
runtime, not those import settings. The owner’s post-import format test is separate
from this integration and cue-admission evidence.

```sh
XDG_DATA_HOME=/workspace/scratch/yuga-batch2-qa/integration-r5/user \
godot --headless --fixed-fps 60 --verbose --path games/yuga-native \
  --script res://tests/mythic_integration_cases.gd -- \
  --report=/workspace/scratch/yuga-batch2-qa/integration-r5/report.json
```

- Canonical test SHA256: `59dd2dbba285f38472c00d26a28e5a7954160abfc05a62b712524f520fc49eaa`.
- Final 97-case report SHA256: `2a888c2f18e98e782aaea9342a083339064e5350ab0950d8c5d72eace800e770`.
- Corrected world SHA256: `81bbe6eb298bdef50bc0ec124578a83229fb0c05d8bf32d4a619de50eaa8c376`.
- Final FX SHA256: `61fb144275d52ba5705404201de5f7c99a0826d1eb233512343ff408d5a602d6`.
- Session SHA256: `89958d9afea47aca96ce2fd98421569f554f15fe4d18a58efe9bacce92090ee9`.
- Player SHA256: `a4742d0bcd11e79b697fd28813b8164d35aaf7c826a288e40c6420661b57848b`.
- All 29 source entries are in `final/report.json`; no source hash drift.

Contract probes were copied from `/workspace/scratch/yuga-batch1-independent/` to
fresh `contracts-r1/` output paths. `contracts/probe-provenance.json` records original
and copied script hashes; only output-path strings changed. Both Godot commands
exited 0 with no errors/warnings. `independent-contract-review.json` checks every row,
the actual runtime source hash, and the final catalogue/schema pins:

- Contract runtime: `7a4e829c35e7d9385c832e0aaeae8b2ba5d380c6c5eaff2a1f9cd0d56a3734e9`.
- Catalogue: `0dd3c82b0fc9b4d7448476bdfaa5d63925173e89ac32169c78208217f25cb1a0`.
- Schema: `fecc47f1cde80f3c37d4ce752e5f7a1f67253824a3eb16287ee90306fb466979`.

## Limits and handoff

These are headless numerical, actual-receiver, control-routing and lifecycle checks.
No human viewed a new render, listened to cues, played an online match or benchmarked
hardware in this review. Visual/readability acceptance, movement/animation art,
competitive balancing, physical keyboard/OS play and packaging are separate gates.
Native player health, core spell damage, new playable hero rigs and native online
authority remain outside this invocation-practice implementation.

Root owns capture review, evidence registration, release/package decisions and the
next milestone. Independent reviewer is available for bounded package verification.
