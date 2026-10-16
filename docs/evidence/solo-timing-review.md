# Solo timing patch review

Patch: /tmp/andolan-solo-timing.patch
Patched scratch copy: /tmp/andolan-solo-timing
Unmodified-source comparison copy: /tmp/andolan-solo-timing-baseline
No repository files changed by the reviewing agents. Root subsequently integrated the patch in `7cf1f27896c580f5f87d289227b817a8563275b8`; all 51 repository tests, typecheck, lint and production builds passed. Temporary paths above describe the original review; the permanent regression tests are `tests/solo-timing.test.ts`.

## Change

Use performance.now() to accumulate elapsed wall time while keeping Simulation.step(0.05). Each advance adds at most 250ms plus a prior substep remainder; this permits at most five 20Hz steps, retains only a remainder below 50ms and discards excess debt. Publish one snapshot after a batch. Advance before accepting fresh input or commands so fresh intent is not backdated over the accumulated interval.

Simulation.clearInput deletes stored intent without altering accepted sequence or vehicle ownership. Expire intent after more than 350ms of actual elapsed wall time. The expiry is conservative for the whole batch: stale controls sacrifice up to 250ms of historical movement rather than simulate an unknown history; existing momentum still coasts. Hide/show resets timing and clears intent, hidden time does not advance the solo world, blur clears intent, and close removes listeners/timers and ignores subsequent actions. Periodic saves use a five-second wall-clock interval checked while visible; commands, hiding and closing also save; a stalled callback writes at most one periodic save.

## Verification

Patched scratch run: `npx vitest run tests/solo-timing.test.ts tests/connection.test.ts` passed two files / 18 tests: nine new timing tests and nine existing online connection tests. `npx tsc --noEmit` and targeted ESLint passed. The systems reviewer independently inspected and reran the same checks successfully.

The nine timing cases cover:
- walking distance and 20 ticks in one second with 50ms versus 200ms callbacks;
- matching acceleration, coasting speed and position under both schedules;
- new movement intent received after 200ms does not move the preceding 200ms;
- five-second stall runs at most five steps, clears stale movement, drops debt and preserves monotonic input sequence;
- 500 ms stale throttle causes coasting, not renewed acceleration;
- hidden pause and clean resume;
- focus loss clears intent while preserving sequence;
- periodic saves follow wall time under load and do not burst;
- idempotent close removes timers/listeners and rejects late actions.

The same walking and acceleration/coasting tests were run against a separate copy of the unmodified source. Both failed, as expected: delayed walking produced 5 ticks instead of 20, and delayed acceleration diverged. Seven unrelated timing tests were deliberately unselected for that baseline run. This demonstrates the regression cases catch the actual fixed-callback defect; the failing baseline is not a failing patched check.

## Limits and traps

- Catch-up does not make rendering faster. Sustained callback gaps over 250ms intentionally remain slower than wall time; the cap prevents unbounded work and unattended travel.
- Input ordering is quantized to 50ms physics ticks; this is not a reconstruction of exact historical input inside each tick.
- Background solo play is paused. Returning resumes momentum without held throttle until fresh controls arrive.
- The separate multiplayer server timer is unchanged; do not claim a server timing fix.
- Browser campaign evidence must be rerun after applying this application change. Scratch tests do not establish rendered comfort or full campaign completion.
