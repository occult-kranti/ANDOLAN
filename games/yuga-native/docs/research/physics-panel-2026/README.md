# Hanuman vault and airborne hit volumes · physics review

This review fixes two issues in the Rust Confluence authority. A Hanuman knocked out while vaulting could retain the vault's height after interruption, causing the next cast to be rejected as airborne. The interruption now clears that height. Attacks also treated every other fighter as grounded. Hanuman's sectors and disks now evaluate the target's actual feet elevation and body height against the authored vertical range. Existing action clocks, damage amounts, cooldowns, event format and horizontal movement remain the same. [Authority](../../../../yuga-rust/src/combat.rs) · [Player input and timing](../../../art/hanuman-hero-finish/GAMEPLAY.md)

## Five review rounds

1. **Reproduce.** At baseline `d1cad241`, two players walked to a clear area. One delivered eight ordinary attacks, then struck while the other used Maruti Udayana. The knockout occurred at 1.3777777 m above ground. A second normal-input duel struck an opponent at 1.530864 m even though the gada's authored height is 1.4 m. [Knockout failure](baseline-midair-knockout.txt) · [Airborne target failure](baseline-airborne-target.txt) · [Duel tests](../../../../yuga-rust/tests/battle.rs)
2. **Choose the contract.** Cancelling or interrupting the vault returns its offset to ground. A started cooldown and the event history remain intact. Hanuman's area hit tests the recipient's vertical capsule against the ability's inclusive height band. Position and elevation are captured together before each fixed tick, so seat processing order cannot change the sample.
3. **Implement.** `Combat::interrupt` clears the casts and resets height. The match authority supplies an internal elevation snapshot keyed by existing receiver IDs. Existing `set_receivers` callers and army units default to ground. The public receiver structure and wire snapshots keep their existing shape. [Combat authority](../../../../yuga-rust/src/combat.rs) · [Match authority](../../../../yuga-rust/src/battle.rs)
4. **Challenge.** In ordinary-input six-seat tests, a target at 1.0716 m is hit and one at 1.5309 m clears the 1.4 m gada volume, for both teams. Airborne allies remain inside the 1.6 m shield band. Separate native-versus-Wasm traces compare 960 seat snapshots for airborne hits and 282 for knockout/respawn. Maximum numerical difference in each was 0.0000000596. [Airborne parity](airborne-parity.json) · [Knockout parity](vault-parity.json) · [Six-player tests](../../../../yuga-rust/tests/team_battle.rs)
5. **Integrate.** The locked Rust suite passed 73 tests, with two existing tests ignored. Native/Wasm room parity checks also passed. Rebuild the browser game so the packaged Wasm includes the changes, then test the downloaded package and room clients separately after packaging. [Rust test output](full-rust-tests.txt) · [Duel parity](duel-parity.json) · [Six-player parity](team-parity.json)

The vault currently uses a 20 Hz authority clock with a 4-tick windup, 9-tick travel and 4-tick recovery. Its `impact` event at release acknowledges takeoff. Visual landing should follow the authority's `landed_age_ticks` and ground height, including an early stop at cover. The corrected code keeps those published semantics. [Ability profile](../../../assets/design/hanuman-ability-kit.json) · [Action state](../../../../yuga-rust/src/combat.rs)

## Reproduce

From the repository root, use Rust 1.88 with the `wasm32-unknown-unknown` target, Node and cached locked dependencies.

```sh
cargo test --locked --offline --manifest-path games/yuga-rust/Cargo.toml
cargo build --release --locked --offline --manifest-path games/yuga-rust/Cargo.toml --bin room
cargo build --release --locked --offline --manifest-path games/yuga-rust/Cargo.toml --target wasm32-unknown-unknown --lib
node games/yuga-native/docs/research/physics-panel-2026/test-vault-parity.mjs
node games/yuga-native/docs/research/physics-panel-2026/test-airborne-parity.mjs
node games/yuga-rust/tools/test_room_parity.mjs --report /tmp/yuga-duel-parity.json
node games/yuga-rust/tools/test_squad_parity.mjs --report /tmp/yuga-squad-parity.json
```

The parity traces start a native room process and a Node-hosted Wasm authority, send both the same player commands and compare the six-seat snapshots. The tests exercise the authority protocol locally. Browser rendering, physical network conditions, human feel and performance remain separate checks. The earlier Hanuman studio release predates these changes.

Rama's projectile and ward calculations keep their existing vertical behavior. A later design pass should specify their capsule and field rules separately, then measure ranged counterplay and test network parity. Static cover and obstacle sweeps still use the ground plane. [Rama projectile test](../../../../yuga-rust/src/rama.rs) · [World authority](../../../../yuga-rust/src/world.rs)

## Design references

- An action owns temporary state that needs cleanup on exit, as in state-machine entry and exit actions. The implementation keeps YUGA's existing action model and applies the cleanup at its current interruption entry point. [Game Programming Patterns · State](https://gameprogrammingpatterns.com/state.html#enter-and-exit-actions)
- A fixed simulation step allows rendering to advance at a different rate. Consistent input sequencing matters for comparison across authorities, and floating-point outputs still need measured tolerance. [Fix Your Timestep](https://gafferongames.com/post/fix_your_timestep/)
- YUGA's world sweeps a disc against its authored cuboids and uses a ground-plane line query for cover. This review leaves the current Parry shape-cast logic and map geometry intact. [Parry shape casting](https://docs.rs/parry2d/0.17.6/parry2d/query/fn.cast_shapes.html) · [YUGA world](../../../../yuga-rust/src/world.rs)
