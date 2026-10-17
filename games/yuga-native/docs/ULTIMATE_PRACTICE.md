# Native invocation practice

Fourteen named invocations can apply real effects to living native lane troops through the current Rama avatar. This is an offline practice adapter, not fourteen production character models or a native online hero roster. The separate [native rules](../assets/design/native-ultimate-rules.json) define damage/support geometry and tuning; [the creative codex](hero-design/README.md) remains presentation-only and its browser baselines are unchanged.

The shared practice cooldown is **12 seconds** for every invocation. Changing the selected name cannot bypass it. Only one gameplay invocation runs at a time; four concurrent effects are a separate renderer stress fixture. Player health, player shields/healing, spell damage to cores, hero swapping and network authority are outside this adapter.

## Implemented troop payloads

All distances are metres. All payloads recheck living teams and line of sight against the army's static XZ boxes. Ground-root centres, with a 2.5 m height band, define this native practice hit test. It does not replace browser fan/cone rules or native primary-fire capsule collision.

| Invocation | Exact practice footprint | Troop effect |
| --- | --- | --- |
| Rama | Three swept arrows, range 28, radius 0.5, speed 62; yaw offsets −0.12/0/+0.12 radians | 32 damage per arrow; first enemy or wall stops each arrow |
| Ravana | Caster disk, radius 7 | 90 enemy damage |
| Arjuna | One swept arrow, range 28, radius 0.5, speed 62 | 88 enemy damage; no piercing |
| Duryodhana | Forward sector, range 12, half-angle cosine 0.55 | 92 enemy damage |
| Hanuman | Clear aimed point within 14; landing disk radius 7 | 65 enemy damage and up to 45 allied healing |
| Karna | Caster disk, radius 6 | 95 enemy damage |
| Bhima | Caster disk, radius 8 | 92 enemy damage |
| Meghnad | Forward sector, range 22, half-angle cosine 0.25 | 78 enemy damage |
| Sita | Fixed caster disk, radius 8, active 6 seconds | Initial 70 shield; allies remaining inside recover up to 9 health/second |
| Draupadi | Caster disk, radius 8 | Up to 95 allied healing |
| Subhadra | Two validated nearby lane placements | Two temporary bow sentinels, 105 health and 28 attack damage each, lasting 9 seconds |
| Hidimbi | Two validated nearby lane placements | Two temporary spear sentinels, 105 health and 32 attack damage each, lasting 9 seconds |
| Chitrangada | Caster disk, radius 6 | 80 allied shield for 4 seconds |
| Ulupi | Clear aimed point within 23; disk radius 7, active 6 seconds | 12 enemy damage/second and actual movement multiplier 0.55; slow expires within 0.5 seconds after leaving |

Hanuman projects a landing payload after preparation/travel; the avatar does not teleport. The temporary sentinels use existing troop models and actual army target/attack/route logic. They cannot damage cores on arrival or award gold on expiry. A pair spawns atomically or fails with a reason if routes, occupancy or capacity no longer permit both units.

Shields absorb before health and use the larger current amount rather than additive stacking. Healing is capped and cannot resurrect. Slow affects actual route displacement and restores speed on expiry. A thin extra bar shows a troop's active shield. Confirmed player-attributed enemy last hits retain the existing once-only gold callback.

## Input and integration boundary

The world owns the selector, key mapping, camera ray and player pose lock. [ultimate_session.gd](../scripts/ultimate_session.gd) exposes:

```gdscript
configure(army: Node3D) -> bool
select_invocation(hero_id: String) -> bool
request_cast(origin: Vector3, forward: Vector3, ground_target: Vector3) -> Dictionary
set_suspended(value: bool)
cancel_active(reason := "cancel")
reset(reason := "reset")
report() -> Dictionary
```

`request_cast` returns `accepted`, `reason`, `epoch` and `cast_id`. It rejects paused/ended rounds, active cooldowns, airborne origins, invalid directions, blocked/out-of-range ground points and unavailable summon pairs before consuming a cooldown. The grounding tolerance is 0.35 m above the army ground plane. Unknown selections do not replace the current choice.

`cancel_active` clears pending payloads, statuses, summons and presentation while preserving cooldown. Use it before teleport/travel shortcuts. `reset` is for an explicit round restart and invalidates the epoch and cooldown. Successful reconfiguration clears effects on the old army before changing the reference; failed configuration preserves the old session.

`report()` returns a detached `selected_rule`, `selected_hero`, `selected_range_m`, `target_kind`, `cooldown_remaining`, `active_phase`, `suspended`, bounded counters and `last_reason`. UI should display these values rather than running its own cooldown clock. It must say **invocation practice** and keep the current avatar identity clear.

Pause/focus/overview integration must suspend the world/army and presentation together. The session advances from the army's accepted 20 Hz `simulation_stepped` signal, not a wall-clock timer; suspension rejects new casts. Army reset and outcome invalidate pending work. A reset requested inside a defeat callback invalidates the invocation immediately and defers freeing locked signal emitters until the callback unwinds. No old receipt may appear in the new epoch.

## Presentation event contract

`invocation_event(event: Dictionary)` is a local Godot signal, not a network protocol. Each event contains:

- `schema`, `kind`, `epoch`, `cast_id`, `event_seq`, `hero_id`, `effect_id`, `team`;
- session `time_s`, cast `age_s`, immutable `origin`, `forward`, `target` vectors;
- `timing`, exact `geometry`, bounded receiver `receipts`, and `reason`.

Kinds are `begin`, `release`, `impact`, `tick`, `end`, `cancel` and `reset`. Begin supplies the exact warning footprint. Release ends preparation. Impact/tick report actual accepted receiver changes. End/cancel/reset retire the presentation. Sequence numbers increase within an epoch; reset starts a greater epoch and resets its sequence to 1. Consumers must reject stale epochs, duplicate sequences and mismatched casts.

Geometry types are `projectile_volley`, `disk`, `sector`, `zone_disk` and `summon_pair`. Their fields come from the native rules, with world `origin`, `center` and `forward`. Projectiles add fixed `projectiles[{index,origin,forward}]`; each contact event adds `projectile_index`, `contact_position` and a unit/wall/range reason. A wall and the last partial lifetime step both participate in the actual swept test. Summon geometry includes the two prevalidated placements.

Ward/summon ticks include `geometry.attachments`: current living recipient IDs/positions and shield amount or remaining lifetime. Absent IDs retire their attachment. Receipts combine multiple effects on one receiver, so a damage-plus-slow tick cannot double the 72-receiver cap. History retains at most 64 events. Effects/audio must consume these events without mutating units; UI and effects must not use the codex's decorative width as a damaging fan or cone.

## Source and receiver ownership

| File | Responsibility |
| --- | --- |
| [ultimate_rules.gd](../scripts/ultimate_rules.gd) | Bounded JSON loading, duplicate-key/depth checks, source/identity/scope/timing validation and planar geometry helpers |
| [native-ultimate-rules.json](../assets/design/native-ultimate-rules.json) | Separate versioned native practice tuning; codex hash, exact geometry, typed payloads and limits |
| [ultimate_session.gd](../scripts/ultimate_session.gd) | Selection/cooldown, cast clock, sweeps, receiver eligibility and bounded events |
| [lane_minion.gd](../scripts/lane_minion.gd) | Real capped healing, shield absorption/expiry, movement slow and temporary-unit overrides |
| [lane_army.gd](../scripts/lane_army.gd) | Fixed-step status/expiry, actual slowed movement, atomic pair placement, existing damage/reward and reset lifecycle |

Ordinary waves retain 72 living units, 24 corpses and 96 total unit roots. Summons share those limits and existing route/grid/target handling. No imported commercial-game code or new art dependency is introduced by this adapter.

## Verification

From the repository root, after the native toolchain and existing assets are available:

```sh
godot --headless --path games/yuga-native --script res://tests/ultimate_cases.gd -- --report=/tmp/yuga-ultimate-cases.json
godot --headless --path games/yuga-native --script res://tests/lane_army_cases.gd -- --report=/tmp/yuga-lane-army.json
godot --headless --path games/yuga-native --script res://tests/siege_army_cases.gd -- --report=/tmp/yuga-siege-army.json
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tools/test-relay-integration.gd -- --report=/tmp/yuga-relay-integration.json
```

The owner suite passes 77 headless checks at this checkpoint: all fourteen real payloads, malformed rules/input, exact sector/disk boundaries, final projectile travel, capped healing/shields, slowed displacement and expiry, summons/capacity, shared cooldown/cancel, repeated restarts and a reset during a defeat callback. The existing lane-army suite passes 21 checks including its 20-minute simulated soak. The siege-army suite also passes 31 checks including its 20-minute simulated soak; relay control passes 42. [The gameplay evidence archive](evidence/mythic-batch2/gameplay/REVIEW.md) retains reports, actual logs and the independent counterexample repairs. Actual-world relay layout and final cross-module integration are recorded by the root-owned integration gate.

These are behavior and lifecycle proofs. Actual selector/input review, moving effect/animation review, sound listening, consumer-hardware profiling, competitive balance, native multiplayer and production character quality remain separate gates. Generated or scripted effects do not establish parity with the reference games.
