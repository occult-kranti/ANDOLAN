# Fourteen heroes in the Rust sparring lab

YUGA’s classic Rust sparring mode plays all 14 original heroes, their primary attacks and all 42 classic abilities on the Sangam City map. The browser uses the existing PlayCanvas renderer, original skinned hero rigs, cast clips, HUD and audio. An allied Rama starts injured at your side and an opposing Ravana stands three metres ahead. Damage, shields, healing, cooldowns, summons, defeat and respawn come from a local Rust WebAssembly instance. The same authority runs as a Rust console program. [Browser ZIP](../../../../yuga-rust/downloads/yuga-rust-classic.zip) · [Browser adapter](../../../../yuga/client/classic-rust-connection.ts) · [CLI](../../../../yuga-rust/src/bin/roster.rs)

## Play in the browser

Extract the entire ZIP. In the directory containing `index.html`, run `python3 -m http.server 8000 --bind 127.0.0.1` and open `http://127.0.0.1:8000/`. Select a hero, then choose **Hero sparring**. Move with WASD, aim with the mouse, use Space to jump, hold the primary button or F to fire and press Q/E/R to cast. **Reset drill** restores the same hero, opening positions and cooldowns. Choose **Change hero** to return to the roster. [Distribution and package verification](CLASSIC-DISTRIBUTION.md) · [Original roster and abilities](../../../../yuga/shared/heroes.ts)

The adjacent **Play with bots** and **Online team match** entries use the original six-seat TypeScript rules. The separate Rust Confluence package offers the enhanced Rama and Hanuman kits, advancing armies and a two-seat opposing-player match. These different game modes share artwork and have distinct action bindings and objective rules. [Classic team modes](../../../../yuga/README.md) · [Confluence build](../../../../yuga-rust/downloads/yuga-rust-confluence.zip) · [Two-seat authority](../../../../yuga-rust/src/battle.rs)

## Play the console

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

The differential driver runs the actual TypeScript `ArenaSimulation` and the compiled Rust executable. It isolates three actors from waves, towers, pickups and jungle events, then compares 42 ability scenarios, 14 primary-attack scenarios and 14 movement scenarios for **70 passing cases and 690 matching snapshots**, with absolute floating-point tolerance 0.0001. It checks health, shields, action phases, all cooldowns, projectile coordinates and velocities, field lifetimes, summon expiry, rejects and recasts. Rust unit tests also cover wall corners, projectile height, shield absorption against another player’s attack, a defender leaving a locked landing, and valid state after rejected commands. [Parity receipt](classic-roster-qa.json) · [Executable differential test](../../../../yuga-rust/tools/test_classic_roster.mjs) · [Geometry and regressions](../../../../yuga-rust/src/bin/roster/geometry.rs)

```sh
npm ci
node games/yuga-rust/tools/export-classic-roster.mjs --check
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster
node games/yuga-rust/tools/test_classic_roster.mjs
```

To refresh the export, run the exporter without `--check`, repeat the differential suite and commit the JSON alongside its donor changes. The level-one sparring rules run independently of towers, jungle, gold, upgrades, native vehicle waves and multiplayer reconciliation. Summons use the middle lane and pursue visible targets. To admit another hero to Confluence, select an enhanced kit, test its rig and ability poses in that renderer, then replay its counters and effect receipts from both player seats. [Full port roadmap](FULL-PORT.md) · [Enhanced Hanuman reference](../COMBAT.md)

The native/Wasm comparison executed 70 cases, matched **690 snapshots** and compared **55,111 numeric values** with zero observed difference. Its edge cases cover buffer limits, memory growth, independent sessions, stable effect IDs, rejected commands and bounded event history. The package test reopens the real ZIP, checks model digests against the canonical manifests and executes all 42 abilities using the Wasm bytes recovered from that build. [Wasm parity receipt](classic-wasm-qa.json) · [Archive receipt](classic-web-package.json) · [Graphical test](../../../../yuga/tests/classic-rust.e2e.ts) · [Packaged-browser smoke test](../../../../yuga/tools/smoke-classic-rust.mjs)

In Chromium, the ordinary roster loaded all **14** full skinned hero rigs with **163–164 bones** apiece. The graphical run exercised **22 casts**, including Q/E/R, movement and primary fire on Rama, Ravana, Subhadra and Ulupi. A separate 1280 × 720 browser run opened the extracted ZIP through a nested HTTP path, loaded 21 model assets and observed the rival’s HUD health fall from 390 to 371. The run recorded no failed or out-of-path requests. These checks cover the practice clinic’s loading, controls, feedback and rendering on the test machine. Hardware frame-time qualification and multiplayer roster admission remain separate roadmap gates. [All-hero graphical receipt](classic-graphical.json) · [Packaged browser receipt](classic-production.json) · [Gameplay capture](classic-gameplay.png)
