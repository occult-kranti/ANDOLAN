# Rama's native ability kit

This module implements one fixed Rama kit in offline native play. It adds actual arrow damage, a collision-limited movement request and protection/healing for the hero and allied lane troops. `rama_vitals.gd` is the hero damage/death/respawn receiver. The world explicitly connects practice hazards to that receiver; the kit does not claim online authority or make every lane soldier target the hero.

The runtime source of labels and tuning is [`rama-ability-kit.json`](../assets/design/rama-ability-kit.json). These are original mythology-inspired game mechanics, drawing on Rama's bow and protective duty. They are not claims of canonical powers. Values remain tuning hypotheses.

| Input default | Ability | Preparation / recovery | Cooldown | Actual effect |
| --- | --- | --- | --- | --- |
| LMB | Kodanda | .18 / .22 s | .40 s | 28 damage, 40 m range, 60 m/s; first enemy stops the arrow. Movement during draw is supported through the release-origin sampler. |
| Q | Piercing Dawn | .65 / .30 s | 6 s | 70 damage, 38 m range, 52 m/s; up to six different enemies, once each. Solid cover stops it. |
| E | Measured Step | .10 / .25 s | 5 s | Requests a 4.5 m collision-limited step over .22 s. The player movement receiver performs the actual swept move. No damage or invulnerability. |
| C | Guardian Circle | .55 / .30 s | 11 s | Fixed 5 m circle within 16 m; 55 shield on entry and 10 health/s for 4.5 s. Hero and allied troop receivers must be inside, on the same floor and visible from the centre. |
| X | Dawn Volley | .95 / .55 s | 18 s | Three 82-damage arrows, separated by .10 s and ±.105 rad; 30 m range at 34 m/s. Each stops independently at its first enemy or cover. |

Saved input bindings own the displayed key labels. The old fourteen-invocation system remains a separate implementation; it does not define Rama's fixed kit.

## Gameplay and integration contract

`RamaAbilityKit` is a Node3D. The world adds it to the scene and calls `configure(army)`. The army is the sole gameplay clock through `simulation_stepped(delta)`; values must be positive and no greater than .05 s. `simulation_reset(reason)` resets the kit, and `outcome(winner)` retires active casts.

The minimal army interface consists of `configured`, `winner`, `elapsed`, `units`, `boxes`, `actor_bounds`; the three signals above; and `line_clear`, `segment_wall_fraction`, `_blocked_with`, `to_local` and `to_global`. The current lane army satisfies it. A practice adapter can expose actual courtyard targets through the same receiver contract.

Call `request_ability(id, feet_origin, horizontal_forward, ground_target, options={})`. Accepted results contain `accepted`, `cast_id`, `generation`, `windup_s`, `recovery_s` and `reason`. Rejections do not spend cooldown. Cooldowns start at acceptance and survive cancellation. There is one actor draw/recovery lock, while previously released arrows and fields may coexist. At most twelve casts exist and history retains at most ninety-six events.

Configure these narrow adapters:

- `set_origin_sampler(callable)` returns the current hero feet position once at Kodanda release. Direction remains locked. Nonfinite, airborne, obstructed or more-than-four-metre displacement cancels that draw.
- `set_muzzle_sampler(callable)` returns the actual current `arrow_muzzle` socket position once at each projectile release. It must be finite, at least .4 m above the feet and within 3 m, with a clear path from the caster. Without this adapter the component uses a 1.25 m fallback. The same sampled position drives projectile sweep and visual travel.
- `set_movement_receiver(callable)` receives `(origin, destination, duration)` at Measured Step release. It returns `{accepted: bool, destination: Vector3}` after starting a real collision-aware movement operation. The kit does not teleport the player.
- `set_hero_receiver(vitals, position_sampler)` connects Guardian Circle to the actual hero receiver. Hero receipts use `receiver_kind: "hero"` and `unit_id: 0`; troop IDs remain their real army IDs.

`cancel_windup(reason)` cancels only the currently preparing, unreleased cast. Previously fired arrows and an established ward continue. `cancel_active(reason)` retires all casts for death, teleport, title return or round teardown. `set_suspended(true)` freezes the gameplay clock; the world should suspend presentation and vitals consistently. `reset(reason)` increments generation, clears cooldowns and retires old effects.

The army runs at 20 Hz. A .18-second preparation releases on the first tick at or beyond that threshold, normally .20 seconds. `release_age_s` records the actual accepted release. Projectile travel starts from that event, so a draw cannot quietly deal damage before its visible release. Motion is a consumer of begin/release/cancel events and cannot release damage by reaching an animation frame.

`ability_event` emits immutable snapshots with `schema`, `kind`, `generation`/`epoch`, `cast_id`, `event_seq`, `ability_id`, `time_s`, `age_s`, `release_age_s`, `origin`, `forward`, `target`, `timing`, `geometry`, `duration_s` and `receipts`. Kinds are `begin`, `release`, `impact`, `tick`, `recovery`, `end`, `cancel`, `reset`. **`recovery` means actor recovery has completed.** Every live cast emits a clock tick at 20 Hz. Indexed projectile impacts additionally contain `projectile_index`, `contact_position`, `terminal`, and `reason`. Piercing contacts are nonterminal until the sixth receiver or cover.

Receivers use the existing `take_hit`, `apply_shield` and `receive_heal` methods; therefore lane kills and gold use existing army receipts. Sweeps include actual unit hull radii and stop at exact first cover contact. Teammates never receive arrow damage. Ground fields also perform line-of-sight checks. No decorative VFX object participates in collision or reward decisions.

Guardian cleanup restores the prior shield contribution only while the current expiry still identifies its grant. Stronger independent shields are not overwritten. A prior weaker shield with a longer duration is restored when the field expires or cancels. The existing minion status API does not attach source IDs, so an independent simultaneous grant with identical amount and expiry cannot be distinguished perfectly; this is a receiver limitation, not a claim of general multiplayer status ownership.

## Hero vitals

`RamaVitals.configure(army)` connects its clock and reset. Maximum health is 300; shield is capped at 100. `receive_damage(amount, source_id, expected_generation=-1, sequence=-1)` returns an accepted receipt and optionally rejects stale generation or repeated source sequence. `receive_heal`, `apply_shield`, `set_suspended`, `reset`, `respawn` and `report` are public.

Signals are `damaged(receipt)`, `defeated(receipt)`, `respawn_ready`, `respawned` and `changed`. Damage consumes shield before health. Defeat occurs once at zero health. Healing does not resurrect. After three running army seconds, `respawn_ready` fires once; `respawn()` restores health and increments generation, and the world restores position/input/ammo. The world must keep vitals ticking while dead. Pause freezes this timer.

## Original visual construction

`RamaAbilityEffects.consume_event(event)` is a bounded event consumer. Its only runtime dependencies are the event data and the original `rama_ribbon.gdshader`. It contains no army/player receiver reference and no damage calls.

Kodanda uses a small curved nock marker, gold arrow and split blue feather wake. Piercing Dawn gathers two smooth helical filaments into a narrow arrow. Measured Step lays two curved sash ribbons along the accepted path. Guardian Circle uses six low shelter arches, an exact open ground boundary, and position-following marks on actual shield recipients. Dawn Volley gathers three curved iris vanes and collapses them into the three separately timed arrows. Contact feedback uses a brief curved bloom at the accepted contact point.

Curves are original cubic Bézier and analytic constructions, rebuilt at up to 30 Hz; projectile transforms and shader phase advance smoothly between authority updates. The renderer extrapolates at most one .05-second army tick. A delayed presentation frame cannot create an unreleased projectile. The shader uses an explicit phase uniform, not global `TIME`, so pause also freezes ribbon motion.

The cap is twelve casts and eighteen pooled contact blooms. Expired contact meshes are reused within that same eighteen-object allocation cap. There are no lights, particles, voices, opaque solar disks, camera shake, screen textures or full-screen flashes. Reduced effects removes secondary contours while retaining the actual warning. Reduced motion freezes ribbon oscillation/rotation and contact growth while preserving travel, release, boundaries and expiry. A missing end event has an eight-second watchdog. Invalid, duplicate, stale, mutated-geometry and retired-generation events are rejected.

## Verification and remaining evidence

Run the meaningful component suite from the repository root:

```sh
godot --headless --path games/yuga-native --script res://tests/rama_ability_cases.gd -- --report=/absolute/fresh/rama-abilities.json
```

It exercises real lane units, actual hero receivers, release timing, swept cover, six unique pierce recipients, movement callback timing, guardian healing/shield ownership, staggered volley, independent cooldowns, pause/cancel/reset, duplicate/invalid events and finite presentation lifetime. Reports pin the source hashes actually tested. World input integration, authored motion, forward-rendered appearance and performance require their own current-source evidence; a passing headless suite does not prove visual finish or competitive balance.

The prior `mythic-ultimates-render-r3/still-rama.png` was directly inspected before this implementation. It shows sparse standing bow outlines and long hairline lane warnings. That historical image is an explicit baseline, not evidence for these new continuous ribbons or real gameplay effects.

The real-world capture helper uses normal Confluence runtime entry points and actual lane receivers:

```sh
python3 games/yuga-native/tools/run-rama-gameplay.py --output /absolute/new/rama-preview --preview --display 128
python3 games/yuga-native/tools/run-rama-gameplay.py --output /absolute/new/rama-gameplay --display 128
```

Reserve the shared renderer, import the final hero, and freeze runtime source first. Preview captures release/contact studies and ends early; full mode records five separate complete ability takes, 363 frames at simulated 30 fps, plus separate low-angle replays and actual hit/defeat/respawn stills. Those deliberate scene-reset cuts are documented in the report. Both modes retain real receiver receipts and before/after source hashes. Full mode verifies the encoded frame count and decodes the entire silent video. Neither mode is a human-input or real-time-performance claim.
