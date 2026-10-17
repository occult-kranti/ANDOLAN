# MYTH08/09/10 independent integration plan

Round 1, 2026-10-17. Planning only; implementation is in progress. Owner files are
`tests/mythic_integration_cases.gd` and this scratch directory. No runtime edits,
imports or renderer activity are authorized here.

## Claims to challenge

- Fourteen selectors represent invocations through Rama, not fourteen playable rigs.
- Every payload mutates living lane troops through real receivers; receipts must
  describe actual before/after health/shield changes and accepted summon IDs.
- Shared 12-second cooldown survives selection, rejected casts, pause and focus loss.
- Army fixed steps alone advance invocation time and status/summon expiration.
- Epoch reset invalidates pending work before numeric unit IDs can be reused.
- Exact warning geometry comes from native rules, not decorative codex widths.
- FX is a bounded consumer; duplicate/stale/cancel events cannot award gameplay.

## Actual-world fixtures

Instantiate confluence_world, disable its automatic army physics and manually step
the real army at 20 Hz. Freeze ordinary fixture movement/attacks where necessary;
retain a separate fixture with real movement for slow/recovery. Do not replace the
session, army, receivers or FX with mocks. Reposition living units only in documented
open native ground; use reset and direct removal for isolated target fixtures.

All fourteen IDs need an actual accepted begin and successful native payload:
damage against enemy commander, capped healing against wounded allied commander,
shield absorbing later real damage, real slow movement, or two actual temporary
units. Verify friendly-fire refusal, unchanged cores and real once-only gold on kills.

## Counterexamples and boundaries

1. Invalid/nonfinite/out-of-map/airborne origin, zero/nonfinite forward, unreachable
   ground target, selection change during cooldown, second cast during activity.
2. Disk exact radius and just outside; finite 2.5 m height band; sector exact range
   and cosine boundary versus nearby excluded direction. Wall corner occlusion
   uses origin (-30,0,-22), receiver (-26,0,-18), adjacent clear receiver (-30,0,-18).
3. Projectile nearest enemy stops each arrow; ally ignored without damage; wall
   wins before behind-wall target; final partial step stops at maximum range.
4. Zone ticks clip the final active delta; leaving/re-entering does not over-tick;
   a dead/freed target cannot resurrect or retain callbacks.
5. Reset during windup, travel, zone and summon activity; reused numeric IDs remain
   unharmed in the new epoch. Repeated resets leave no temporary nodes/statuses.
6. Pause, overview, focus loss, controls modal: cooldown and effects freeze; cast
   rejects without begin. Resuming preserves remaining state rather than resetting it.
7. Shield is max-style, absorbs before health, expires; strongest slow recovers;
   both obey real fixed-step time. Invalid receiver amounts cannot heal or reward.
8. Summon pair succeeds atomically or yields zero. Occupancy changing after begin,
   71/72 live capacity, 95/96 total-node pressure, death and expiry must preserve caps.
   Expiry has no gold/core damage and removes queued attack eligibility.
9. Replay accepted FX event, stale seq/epoch, malformed geometry/receipt, fifth visual
   cast, repeated pause/mute/reset. Compare gameplay snapshots before/after FX-only
   calls. Low-effects warning boundary stays exact; ornament has no authority.
10. Repeated world lifecycle: one session callback and one effects consumer, no
    accumulating nodes/history or callbacks after disposal. Existing siege and relay
    reset/army behavior remains intact.

## Evidence gates

Round 2 retains meaningful failed reports and fixes fixture assumptions explicitly.
Round 3 runs against frozen source hashes, records exact commands and results, and
verifies hashes did not change during execution. No numerical pass establishes visual
quality, human input usability, online play, production balance or hardware FPS.

## Accepted integration names and early challenge resolutions

Root glue: `invocations`, `ultimate_fx`, `invocation_panel`; methods
`cast_invocation()`, `_open_invocations()`, `_close_invocations()`,
`_select_invocation(hero)`. X is the remappable ultimate action; F3 opens practice.
Player preparation is root-owned `begin_invocation(windup, clip)`.

FX: `consume_event`, `step`, `set_suspended`, `set_options`, `reset`, `report`.
Four visual casts, no lights/particles/voices or army references. Use detached IDs.
The FX owner accepted the need for current bounded attachment snapshots from session
so shields/summons follow accepted recipients; omitted IDs must disappear. Per-unit
shield arcs are merged into one mesh to preserve the 48-instance budget.

UI: `configure`, `update_session`, `open`, `close`, `set_notice`, `set_available`,
`report`; `hero_buttons`, `choose_button`, `close_button`, reduced-effects and
reduced-motion buttons are public. Preview is separate from accepted selection.

The Ulupi/Sita 72-recipient case must preserve completeness: combining damage/heal
and slow/shield as separate rows cannot silently create 144 receipts or truncate
accepted mutations. Owner notified before implementation freeze.
