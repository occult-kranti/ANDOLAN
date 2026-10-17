# Rama deliberate input: contract review

Role 08 of the production squad. Baseline inspected: `1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e` on `game/yuga-native-production`.

The observable problem is that `player.gd` ignores discrete Q/E/C/X presses while `invocation_locked` is true. Q, C and X deliberately commit Rama until the army releases recovery. A player tap near the last recovery tick therefore disappears before it reaches `rama_hero_runtime.gd`. Held primary fire has a different contract and is retried by the existing held-input path.

## Bounded proposal

A single deliberate secondary-ability intent can be admitted only during the final 120 milliseconds of an accepted action's recovery. Its lifetime is measured on the same 20 Hz kit/army clock that unlocks combat. The intent contains an ability ID and monotonically increasing input edge token; it does not reserve damage, ammunition, cooldown, position or aim. An actual recovery event can trigger at most one call to the existing runtime request using current aim and position. The normal kit remains the only owner of acceptance, begin/release, damage and cooldown.

A fresh deliberate edge may replace the one pending intent. Duplicate/held/keyboard-echo inputs cannot append, replace or extend it. Cooldown-blocked requests cannot become pending. An edge before the final recovery window cannot become pending. A queued request cannot survive pause, any gameplay modal, suspension, inactive/dead actor, reset, teleport, scene exit, round outcome or combat generation change. Cancellation/hit interruption must clear it rather than turning the interruption into a shortcut to casting. A request attempted at expiry is consumed before invoking external code so reentrant listeners cannot replay it.

## Approved conservative scope

The existing kit checks `action_locked` before geometry. Its public report exposes action ID, phase, age and cooldowns, but does not expose an independent nonmutating geometry validator. A module must not pretend it has ruled out Guardian cover or Step wall failures while busy. Root approved Q/X-only secondary projectiles after finite grounded aim checks; E/C remain immediate. A future shared pure preflight sampler would need its own contract before enabling E/C. The real kit still rechecks every actual execution.

The buffer is not an animation or competitive-balance claim. It is a small input-handling hypothesis requiring a normal-input comparison in the actual game. A deterministic case count can establish lifecycle and timing behavior; it cannot establish that combat feels smooth to a person.

## Integration ownership

Initial ownership covered `scripts/rama_action_buffer.gd`, `tests/rama_action_buffer_cases.gd` and this evidence directory. Root then granted this role temporary exclusive ownership of `player.gd` and `rama_hero_runtime.gd` for the buffer hooks and a new actual-world integration fixture. Those shared files were tested and released back to root; their exact buffer-only snapshots are in `integration/source/`. Root owns subsequent quality-component integration and the source/content manifest revision. No kit rule or protocol changes were made here. Direct `cast_ability` and `kit.request_ability` contracts remain immediate and unchanged.
