# Fourteen heroes in the Rust sparring lab

The `roster` executable plays the original browser roster on the classic Sangam City collision map. Each hero can walk, jump, fire and use all three abilities. The executable supports a text console for players and newline-delimited JSON for replay tools. The graphical edition continues to use its enhanced Hanuman and Rama kits. [CLI entry](../../../../yuga-rust/src/bin/roster.rs) · [Original roster](../../../../yuga/shared/heroes.ts) · [Classic rules](../../../../yuga/shared/simulation.ts)

## Play

From the repository root choose a hero with `--list`. In the console, basic attacks advance the clock in ticks of 50 ms. A cast commits immediately, and a subsequent `wait`, `move`, `jump` or `shoot` advances the action. The initial Moon sparring partner is three metres ahead. The friendly target starts injured so that healing and shields have an observable effect.

```sh
cargo run --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster -- --list
cargo run --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster -- --play sita
```

Try these lines in Sita’s console. Facing +Z is yaw zero. A downward pitch aims at nearby ground.

```text
cast 1
aim 0 -0.35
cast 2
wait 10
cast 3
wait 18
shoot 12
quit
```

For an automated session omit `--play`. The first JSON line is the initial snapshot. Every command produces one new line; `cast` slots are zero-based here. Each command is independent. Movement, fire and jump are held for its `ticks`; yaw persists and pitch defaults to zero. Set `actor` to `self`, `ally` or `enemy` to test counterplay. An unchanged standing actor is still affected by other actors' casts and by fields. Omitting `ticks` commits a cast without stepping the clock.

```sh
cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster -- hanuman <<'JSON'
{"cast":2,"pitch":-0.35}
{"actor":"enemy","movement":[0,1],"ticks":23}
JSON
```

This example lets the defender leave the locked landing before Mountain Descent resolves. Snapshots include actor positions and height, health, shields, cooldowns, cast phase, slow and ward timers, active projectile positions and velocities, summons and zone exposure. Each action returns an acceptance flag. Malformed commands leave the simulation untouched.

## Mechanics exercised

| System | Ported behavior |
| --- | --- |
| Aimed shots | Each hero’s weapon interval, speed and damage. Bolt and line attacks have their own projectile radius, speed and range. Projectiles travel in 3D, hit eligible living units and stop at solid geometry. |
| Directional and radial attacks | Burst and cone apply the source facing thresholds and visibility. Nova checks distance and line of sight. Shields absorb damage before health. |
| Movement and control | Axis-separated horizontal sweeps, gravity, jump edges, slow speed reduction, wall-limited dash/leap and displacement from pull. A leap also supplies vertical velocity. |
| Protection and pressure | Instant heals cap at maximum health. Wards use the greater strength and refresh their duration. Slow fields re-evaluate exposure while enemies remain inside. |
| Reinforcements | Subhadra and Hidimbi summon two actor bodies at valid nearby placements. They aim, shoot, approach on the middle route, take damage and expire after nine seconds. |
| Three distinct ultimate sequences | Rama locks facing and pitch before firing three arrows. Hanuman braces, travels on a vertical arc and damages/heals visible receivers at landing. Sita grants a shield at release and leaves a fixed healing sanctuary. |
| Defeat and sparring reset | Defeated heroes cancel pending casts and respawn after the classic delay, with temporary protection. Eliminated or expired sentinels are removed. Starting a new executable resets the fixture. |

All 42 abilities use the authored `HEROES` profile. A build tool imports the live TypeScript definitions, including helper calls and object spreads, together with the eight classic solids and capacity limits. It records digests of the roster, map and simulation source. Run the freshness check and differential suite after changes to any of these files. [Export and freshness check](../../../../yuga-rust/tools/export-classic-roster.mjs) · [Generated data](../../../../yuga-rust/assets/classic-roster.json) · [Rust abilities](../../../../yuga-rust/src/bin/roster/abilities.rs) · [Movement and simulation](../../../../yuga-rust/src/bin/roster/lab.rs)

## Verification and migration boundary

The differential driver runs the actual TypeScript `ArenaSimulation` and the compiled Rust executable. It isolates three actors from waves, towers, pickups and jungle events, then compares 42 ability scenarios, 14 primary-attack scenarios and 14 movement scenarios for **70 passing cases and 690 matching snapshots**, with absolute floating-point tolerance 0.0001. It checks health, shields, action phases, all cooldowns, projectile coordinates and velocities, field lifetimes, summon expiry, rejects and recasts. Six Rust tests also cover wall corners, projectile height, shield absorption against another player’s attack, a defender leaving a locked landing, and valid state after rejected commands. [Parity receipt](classic-roster-qa.json) · [Executable differential test](../../../../yuga-rust/tools/test_classic_roster.mjs) · [Geometry and regressions](../../../../yuga-rust/src/bin/roster/geometry.rs)

```sh
npm ci
node games/yuga-rust/tools/export-classic-roster.mjs --check
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster
node games/yuga-rust/tools/test_classic_roster.mjs
```

To intentionally refresh the export, run the exporter without `--check`, repeat the differential suite, and commit the generated JSON with its source changes. The level-one fixture omits upgrades, gold, towers, jungle, pickups, native vehicle waves, network reconciliation and hero presentation. Summons use the middle-lane route and visible sparring targets. The suite measures classic ability parity inside this boundary. The next handoff is a single additional graphical hero, with independent rig and ability poses, a counterplay fixture and matched receipts over a two-seat room before expanding roster selection. [Production migration roadmap](../README.md) · [Enhanced Hanuman reference](../COMBAT.md)
