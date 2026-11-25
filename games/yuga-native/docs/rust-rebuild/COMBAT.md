# Hanuman combat in Rust

The Rust training drill loads all five abilities from the existing Hanuman kit. Its 20 Hz simulation owns cast acceptance, collision, damage, shields, cooldowns, delayed impacts and the pose marker used to sample each ability clip. The three opposing receivers stand still so that a player can repeat an attack from the same position. The Sun ally demonstrates Ward targeting. [Rule data](../../assets/design/hanuman-ability-kit.json) · [Rust simulation and tests](../../../yuga-rust/src/combat.rs) · [Ground collision](../../../yuga-rust/src/world.rs)

## Five-round combat panel

| Round | Moderator question | Result |
| --- | --- | --- |
| 1 · Inventory | Which rule set already runs in the game? | Traced Godot's combat authority, actor movement, authored motion library and recorded full/reduced-effect timelines. Selected the existing JSON as the balance authority. |
| 2 · Source audit | What can an existing Rust game contribute? | Inspected the pinned Cave Story implementation, Veloren and Jumpy files below. Chose tick scheduling, action-stage separation and explicit hit ownership as applicable patterns. Retained YUGA's team and combat semantics. |
| 3 · Implementation | Can the rules drive an actual shared game state? | Ported all five actions, action/field overlap, ground target selection, fixed-tick health and cover. Exercised the complete three-target drill. |
| 4 · Cross-review | Do physical landing, cover, delayed damage and animation agree? | Added a ground-validity test, native margin-based vault targeting, release recheck and swept landing. Extracted pose markers from the same animation source as the hero exporter. Verified covered shields, moving receivers, pauses and edge contact. |
| 5 · Acceptance | Which results can the next engineer reproduce? | The commands and cases below identify every exercised combat behavior, what the browser must render and the remaining rollout work. |

## Ability contract

Distances are horizontal metres. A tick is 50 ms. Timings are elapsed since the accepted cast. The shared JSON also sets radii, vertical tolerances, team filters, cooldowns and clip names. [Five ability definitions](../../assets/design/hanuman-ability-kit.json)

| Ability | First commitment | Resolution | Recovery and reuse |
| --- | --- | --- | --- |
| Vajra Gada | At 250 ms, sweep a forward sector of 3.5 m. | Apply 34 damage to each living visible enemy in the sector. | Ready at 550 ms. Cooldown 600 ms. |
| Vajra Kavacha | At 350 ms, raise the ward. | Apply a 48-point shield to the caster and visible allies inside a 5.5 m forward fan for 3 s. | Ready at 600 ms. Cooldown 9 s. |
| Maruti Udayana | At 200 ms, recheck and start the accepted vault. | Cover can shorten the 8.5 m endpoint. A 450 ms parabolic sweep drives position and height. The movement-start impact event carries no damage. | Ready at 850 ms. Cooldown 7 s. |
| Lanka Dahan | At 450 ms, damage enemies behind the original facing. | Deal 28 burst, then 8/s for 2 s to surviving enemies still in the fixed 5 m sector. | Ready at 850 ms. The field can overlap a new cast. Cooldown 11 s. |
| Mountain Pulse | Mark a visible floor position up to 14 m away. Release at 700 ms. | At 1,150 ms, evaluate a 7 m disk. Damage enemies by 65, heal allies by up to 45, test current position and cover. | Ready at 1,650 ms. Cooldown 30 s. |

The Godot build from revision `9898ba749b2be630ba283003c132dc9329c6cba7` provides the source and timing oracle. The Rust regression reads the existing Godot capture directly and checks each event kind and simulation millisecond for every ability in both VFX modes. A match here means timing parity for those specific scenarios. [Native combat](../../scripts/hanuman_combat.gd) · [Native actor](../../scripts/hanuman_actor.gd) · [Recorded scenarios](../research/hanuman-ability-production/QA-integration.json)

## Source-backed reuse decisions

**doukutsu-rs** reimplements the Cave Story engine in Rust. Its weapon tick decrements a refire counter and gates a new shot. Its Polar Star projectile increments age, retires at its lifetime and requests a separate visual cue. This is a useful candidate when Rama gains persistent projectiles. Importing this whole weapon module would also bring pixel-space movement, the original weapon enum and a global game state. Use its small lifecycle boundary to design a YUGA projectile adapter. The engine code is MIT. The original game's media is supplied separately. [Weapon tick](https://github.com/doukutsu-rs/doukutsu-rs/blob/d9a281f959eba3a4423606ec7ddf4b047a1e6ff2/src/game/weapon/mod.rs#L165-L192) · [Polar Star lifetime](https://github.com/doukutsu-rs/doukutsu-rs/blob/d9a281f959eba3a4423606ec7ddf4b047a1e6ff2/src/game/weapon/bullet.rs#L298-L325) · [Engine license](https://github.com/doukutsu-rs/doukutsu-rs/blob/d9a281f959eba3a4423606ec7ddf4b047a1e6ff2/LICENSE) · [Game-data instructions](https://github.com/doukutsu-rs/doukutsu-rs/blob/d9a281f959eba3a4423606ec7ddf4b047a1e6ff2/README.md)

**Veloren** is an original Rust RPG. Its melee state sequences buildup, attack and recovery. Its shockwave creates an event, and the shockwave system keeps a set of receivers already hit. That set is a useful future contract for a moving shockwave or piercing arrow. A fixed Mountain Pulse disk can resolve once at contact. Lanka has intentional repeated exposure, so a single hit-set there would suppress its burn. The source is GPL-3.0. This port uses the existing YUGA implementation as its gameplay source. [Melee states](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/common/src/states/basic_melee.rs#L68-L149) · [Shockwave events](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/common/src/states/shockwave.rs#L165-L265) · [Receiver bookkeeping](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/common/systems/src/shockwave.rs#L135-L188) · [License](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/LICENSE)

**Fish Folk Jumpy** is an original Rust multiplayer platform fighter. Its sword creates an owner-tagged rectangle with a 2/60 s lifetime. A separate system excludes its owner and kills intersecting vulnerable players. YUGA's protections need team checks and a health receiver. Its ward explicitly includes its caster, while its attacks affect enemies. The lifecycle system is a useful reference for expiring visual effects tied to a cast ID. Jumpy offers MIT or Apache-2.0 for code and specifies CC BY-NC 4.0 for its art. This trial uses YUGA hero assets. [Sword region](https://github.com/fishfolk/jumpy/blob/514557dc4b5d596a840d95977e06eae191296a77/src/core/elements/sword.rs#L135-L183) · [Damage receiver](https://github.com/fishfolk/jumpy/blob/514557dc4b5d596a840d95977e06eae191296a77/src/core/damage.rs#L42-L100) · [Lifetime](https://github.com/fishfolk/jumpy/blob/514557dc4b5d596a840d95977e06eae191296a77/src/core/lifetime.rs#L43-L78) · [Code and media terms](https://github.com/fishfolk/jumpy/blob/514557dc4b5d596a840d95977e06eae191296a77/LICENSE)

The executable uses Serde 1.0.229 and serde_json 1.0.154 for the rules and snapshots, each offered under MIT or Apache-2.0. The ground queries call Parry2D 0.17.6 under Apache-2.0. These are linked dependencies. The three games above were inspected as design references. The Rust gameplay implementation draws its values, behavior and motion curves from YUGA. [Dependency lockfile](../../../yuga-rust/Cargo.lock) · [Serde](https://docs.rs/crate/serde/1.0.229) · [serde_json](https://docs.rs/crate/serde_json/1.0.154) · [Parry2D](https://docs.rs/crate/parry2d/0.17.6)

## Rendering and input handoff

The drill starts with Hanuman at X/Z `[0, -55]` facing +Z, with 275/300 HP. Moon receivers 1, 2 and 3 spawn at `[0, -52.5]`, `[0, -58]` and `[2, -48]`. Sun ally 4 stands at `[1, -51.5]`. Each receiver begins with 90 HP.

- The shell calls `cast(slot, ground, world)` once per input edge and `tick(movement, world)` once per authoritative step. Rejected casts preserve cooldown and event state. Movement and aim use X/Z metres. A pause is a period with zero simulation ticks.
- `active.motion` selects the animation. Sample it at `active.motion_phase_normalized * clip_duration`. The time cursor follows windup, travel and recovery as authored. A vault starts at the movement-accepted impact, and the landing pose begins on physical contact. Across a reset, a new cast or a timeline discontinuity, seek directly to the new state.
- `casts` includes live fields after Hanuman regains control. `active` contains only the actor's current locked action. Replay events can be deduplicated by generation plus sequence. The simulation keeps the last 64 events.
- `actor.pos`, `actor.y` and `targets` determine rendering positions. `targets[*].hp/shield` reflect resolved effects. Use `defeated == enemies` to finish the drill. Reset replaces the fixture, increments the generation and clears any pending impact.
- The build reads release and optional contact markers directly from the animation library. Missing marker/ability pairs or conflicting release poses fail initialization. The GLB exporter also carries those markers as extras. [Build-time marker extraction](../../../yuga-rust/build.rs) · [Authored motion](../../assets/heroes/hanuman/hanuman-ability-motion.tres) · [GLB conversion](../../../yuga-rust/src/hero.rs)

The browser starts the Wasm module with `trial_start()` and casts with `trial_cast(slot, gx, gz, aim_x, aim_z)`. Slots 0 through 4 follow the ability order above. `trial_tick(dx, dz, aim_x, aim_z)` advances one step, and `trial_reset()` restores the fixture. Read `trial_snapshot()` then `trial_snapshot_len()`, immediately copy/decode those UTF-8 bytes from module memory, and retain the parsed value. [Wasm ABI](../../../yuga-rust/src/lib.rs) · [Browser client](../../../yuga-rust/web/main.ts)

## Reproduce and extend

From the repository root run the focused test suite with Rust 1.88 or newer.

```sh
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --lib combat::tests
```

| Rust test | Acceptance evidence |
| --- | --- |
| `five_native_action_timelines_match_all_recorded_beats` | Matches every event kind and millisecond for five abilities × two native recordings. Also checks HP, shields and final vault position in the Rust fixture. |
| `active_field_releases_action_lock_and_preserves_one_impact` | Starts Gada while the Lanka field is still alive. Resolves one impact per action plus 40 damage-rate ticks for Lanka. |
| `rejection_cooldown_reset_and_bounded_history` | Rejects invalid slot, nonfinite and out-of-range input. Tests cooldown edge, 32 repeated attacks, 64-event eviction and reset during Mountain flight. |
| `shield_expires_on_authority_tick_and_vault_has_visible_apex` | Checks 48 shield just before expiry at tick 67, exactly zero on expiry, visible vault height and movement lock. |
| `full_drill_can_finish_by_aiming_selective_attacks` | Wins against all three Moon targets while Sun ally survives by combining actions, walking and choosing a new facing. |
| `motion_uses_authoritative_clip_markers_and_pause_does_not_advance` | Samples each release/contact marker, checks the stage and confirms repeated reads of a paused simulation are identical. |
| `occluded_ward_and_receivers_leaving_or_entering_a_delayed_disk` | A corner occludes Ward. One receiver exits Mountain's disk during flight, a second enters and absorbs 48 of 65 with a shield. |
| `floor_limits_prevent_outside_marks_and_bound_the_actual_vault_endpoint` | Rejects outside-floor Mountain targeting, cancels a vault after origin displacement and measures the physical landing against the planned boundary endpoint. |

The first test uses the independently recorded Godot timings as an oracle. The other seven exercise Rust behavior directly. The world suite checks geometry queries separately. [Combat cases](../../../yuga-rust/src/combat.rs) · [World cases](../../../yuga-rust/src/world.rs)

The drill currently uses horizontal wall geometry, a swept disc and a prescribed vertical vault curve. Uneven floors, elevated landing decks, vertical obstructions, hero-vs-hero damage, moving combat AI and network resimulation remain migration work. Start by replaying a receiver moving under ward cover on both backends, then transfer wave-unit state and compare snapshots on a complete lane replay. For multiplayer, record input tick, actor, aim and target, run server authority, and repeat the replay after packet loss and reconnection. Retain this drill as a small regression fixture through those changes.
