# Persistent three-lane armies

Confluence now runs a complete Sun–Moon lane-army match in Rust. Guards deploy, march, acquire enemy units in their lane, fight through the wave, and damage the opposing core when they reach the end. Either core can fall. Simultaneous destruction produces a draw. The same module supplies playable hero targets and a headless match driver. [Shared authority](../../../../yuga-rust/src/army.rs) · [Attack resolution](../../../../yuga-rust/src/army/combat.rs) · [Command-line driver](../../../../yuga-rust/src/bin/lanes.rs)

## Run and verify

```sh
# A complete twenty-minute unattended simulation, with its final state as JSON
cargo run --release --locked --manifest-path games/yuga-rust/Cargo.toml --bin lanes -- --match 24000
# Replay an isolated wave at a chosen age for placement inspection
cargo run --locked --manifest-path games/yuga-rust/Cargo.toml --bin lanes -- 15 1200
# Normal unit tests
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --lib army::
# Includes the archived 24,000-tick stress check and a live Godot formation comparison.
# Install Godot 4.6.3 and import games/yuga-native once for the live comparison.
cargo test --release --locked --manifest-path games/yuga-rust/Cargo.toml --lib army:: -- --include-ignored
```

The persistent mode accepts a tick budget and stops early if the match ends. The two-number mode still runs the cleared-spawn inspection fixture. Both commands use the same Sun/Moon routes, role stats, formation order and lane sampling. [Isolated-wave examples](../ARMIES.md)

## Authority, content and rules

| Concern | Implemented behavior | Source |
| --- | --- | --- |
| Clock and roster | 20 Hz, 30 opening troops, then a wave event every 600 ticks. Each lane tries a ten-unit mirrored infantry group. Every third event also tries a pair of cannon carts per lane. Every fifth tries a central chariot pair. Failed groups leave both factions unchanged. | [Wave construction in Godot](../../../scripts/lane_army.gd#L430) |
| Motion | Route distance, left/right offset, reverse heading, body radius and local unit separation. Lane strips, corner joins and floor bounds are checked when the map loads. Troops preserve native insertion order for occupancy and nearest-target ties. | [Native route sampling](../../../scripts/lane_army.gd#L412) · [Canonical map](../../../assets/world/confluence-map.json) |
| Combat | Decisions at 5 Hz, line-of-sight checks, role-specific range and cooldown, windups, simultaneous damage eligibility, and cancellation when the source dies. Melee and arrows revalidate the target. Vehicles commit to ground so a target can dodge and another enemy can enter the blast. | [Native combat step](../../../scripts/lane_army.gd#L253) · [Unit role stats](../../../scripts/lane_minion.gd#L11) |
| Population | Stable, increasing unit IDs throughout the match. Caps of 72 live units, 24 bodies, 96 total nodes, 72 queued attacks and 32 pending siege attacks. Expired bodies disappear after 24 ticks. | [Native limits and cleanup](../../../scripts/lane_army.gd#L10) |
| Match objective | Each core starts at 100 HP. A spearman/bow guard arrival deals 7, commander 12, cannon cart 20, chariot 25. Both teams’ arrivals settle together. The six tower locations on the native map are scenery. | [Core settlement](../../../scripts/lane_army.gd#L347) |
| Hero participation | Native Sun hero last hits award 18/24/45/70/110 gold by role. The Rust match extends that rule symmetrically to a Moon player. Heroes can heal or shield allies. A shield absorbs damage before health. Only the final hero hit earns the reward. Native troops focus on opposing troops. | [Native reward rule](../../../scripts/lane_army.gd#L516) · [Native status receivers](../../../scripts/lane_minion.gd#L161) |

The reusable foundations are the existing YUGA Godot simulation, original map and imported Parry ground queries. No third-party match logic or character assets were introduced by this port. The Godot role definitions still live in GDScript. The differential test compares the Rust values to the installed engine. [World source and licensing](../WORLD.md)

## Native comparison and measured results

Rust and Godot 4.6.3 matched on live troop count, lane defeats and arrivals, waves, both core health values, active attacks, infantry rejections and siege counters at all ten checkpoints below. A separate trace compared every live unit's ID, health, target, combat state and position for the first 3,000 ticks. Positions agreed within 0.1 mm. The archived native soak also supplies expected peaks and end-of-run defeat and siege totals for the Rust regression test. [Historical Godot evidence](../../evidence/siege-qa/army-final.json) · [Native reproduction fixture](../../../tests/siege_army_cases.gd) · [Rust tests](../../../../yuga-rust/src/army.rs)

| Tick | Live | Defeats, west / middle / east | Sun / Moon core | Siege impacts | Pending attacks |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 30 | 0 / 0 / 0 | 100 / 100 | 0 | 0 |
| 500 | 30 | 0 / 0 / 0 | 100 / 100 | 0 | 0 |
| 600 | 60 | 0 / 0 / 0 | 100 / 100 | 0 | 2 |
| 1,000 | 42 | 6 / 6 / 6 | 100 / 100 | 0 | 0 |
| 1,200 | 70 | 8 / 10 / 8 | 100 / 100 | 0 | 0 |
| 1,800 | 69 | 18 / 21 / 18 | 100 / 100 | 0 | 4 |
| 3,000 | 71 | 39 / 43 / 39 | 100 / 100 | 68 | 7 |
| 6,000 | 72 | 91 / 94 / 91 | 100 / 100 | 148 | 4 |
| 12,000 | 65 | 196 / 202 / 201 | 100 / 100 | 286 | 4 |
| 24,000 | 64 | 400 / 395 / 413 | 100 / 44 | 537 | 3 |

The run spanned 41 wave events and eight central-lane arrivals. There were 556 siege windups and 1,293 blast hits. The controller reached 72 live troops, 9 corpses, 76 total nodes, 20 pending attacks and 5 pending siege attacks at peak. No hero input was sent. A separate scripted player-intervention test wins a complete match through legal troop hits and normal allied core arrivals. A two-team fixture also settles a simultaneous draw and verifies that further input cannot restart the simulation clock.

Two implementation details changed the result enough to warrant regression tests. Godot narrows the lane interpolation fraction to its 32-bit vector scalar before multiplying by the original segment displacement. The earlier normalized-direction calculation put a cannon about 15 micrometres from its native position. At tick 1,258 that difference changed which side of the 1.21 m commander–cart spacing threshold a move fell on. The native vehicle cooldown accumulators also leave a small positive remainder at the nominal threshold. A stationary cart can fire again after 81 ticks and a chariot after 53. Matching these rules recovered the measured native timings and final core health. [Godot Vector3 interpolation](https://github.com/godotengine/godot/blob/4.6.3-stable/core/math/vector3.h) · [Native timing regression](../../../../yuga-rust/src/army/combat.rs)

## Integrating a hero and renderer

Use `Army::load()` at match start. Within each 50 ms tick, get `army.receivers()`, step one hero, and commit that hero's changes with `apply_receivers_for(&receivers, team)`. Repeat against a fresh receiver list for each hero, then call `army.step(&world)` exactly once. Each receiver carries the unit’s immutable ID and faction, position, body height/radius, max health, health and shield expiry. Using the authoritative tick for hero shield clocks preserves expiry during a warm start. `frontline_spawn_for` finds a clear position behind that faction’s central vanguard. `winner()` exposes match completion. [Army API](../../../../yuga-rust/src/army.rs)

The snapshot includes the five troop roles, positions, facing, health, target IDs, animation state, death tick, pending attacks, aggregate economy and both cores. A siege attack includes its muzzle origin, committed point, radius, start and due ticks. Render windups from that fixed point. Ordinary attacks retain the target ID. Use unique IDs for presentation pools because corpse removal can compact the unit array. Gold and kill totals are per faction; individual player economy, consumables, dynamic tower attacks and hero-targeting enemies would require additional game rules. The headless results measure simulation behavior; GPU throughput and network latency have separate verification paths.
