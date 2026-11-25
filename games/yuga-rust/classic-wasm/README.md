# Classic roster browser authority

This module runs the same Rust simulation as the `roster` CLI for all 14 classic heroes and their 42 abilities. It embeds the exported classic roster and Sangam City collision geometry. Each browser instance has its own actors, projectiles, fields, timers and bounded event history. The compiled module has zero host imports. [Shared simulation](../src/bin/roster/lab.rs) · [Playable roster and rules](../../yuga-native/docs/rust-rebuild/deep-search/ROSTER-PORT.md) · [Client asset](../../yuga/client/assets/classic-roster.wasm)

## Build and verify

From the repository root, install the locked Node dependencies, use Rust 1.88 or newer and install `wasm32-unknown-unknown`. These commands check the exported TS definitions, build using this crate's lockfile, refresh the browser asset and third-party notices, and verify the native/portable simulation.

```sh
npm ci
rustup target add wasm32-unknown-unknown
node games/yuga-rust/tools/build_classic_wasm.mjs
cargo test --locked --manifest-path games/yuga-rust/classic-wasm/Cargo.toml --lib
node games/yuga-rust/tools/test_classic_wasm.mjs
```

The build tool locates the Cargo artifact even when `CARGO_TARGET_DIR` is set. Use `--binary PATH` to test an existing native `roster` executable, `--wasm PATH` to test another module or `--report PATH` to save a receipt. Use the checked-in Wasm asset and notices when packaging a client without Cargo. [Build tool](../tools/build_classic_wasm.mjs) · [Parity test](../tools/test_classic_wasm.mjs) · [Third-party notices](THIRD-PARTY.txt)

## Browser interface

| Export | Contract |
| --- | --- |
| `memory`, `roster_input_ptr()`, `roster_input_capacity()` | Write UTF-8 bytes to the fixed 4,096-byte staging area. Reserve no heap memory from JavaScript. |
| `roster_reset(byte_length)` | Start a fresh sparring fixture for the raw, lowercase hero ID in the input area. Returns 1 on success, 0 on invalid input. |
| `roster_command(byte_length)` | Parse one JSON command and return 1 on successful evaluation. A cooldown or cast-in-progress rejection is valid input and its snapshot contains `accepted: false`. Invalid command data returns 0. |
| `roster_snapshot_ptr()`, `roster_snapshot_len()` | Copy or decode the last accepted UTF-8 JSON snapshot immediately. The output length is zero until a hero is selected. Snapshot output is capped at 256 KiB. |
| `roster_error_ptr()`, `roster_error_len()` | Return a UTF-8 description of the last input error. A subsequent successful command clears it. |

For every call, obtain a fresh view of `memory.buffer` if memory may have grown. A failed reset or malformed command preserves the previous published snapshot. Every valid command uses the headless CLI semantics, including ticks of 50 ms, finite angle bounds and a maximum of 3,600 steps per command. Primary movement/fire commands and ability slots can address the selected hero, ally or enemy. Stable zone, projectile and event IDs let the renderer track one cast across ticks. Events carry the actor, team, contact position, time and applicable target, slot and amount. Deduplicate by ID within a session and clear presentation state on reset. [Byte binding and edge tests](src/lib.rs) · [CLI command schema](../../yuga-native/docs/rust-rebuild/deep-search/ROSTER-PORT.md)

## Verified artifact

The release asset measured **225,095 bytes**, with SHA-256 `7070db19fda3d8b15d878259363da6520d9e2dd2eb581e819bb1281a7a6b24a9`. On the tested fixtures, WebAssembly and native Rust produced the same values for **690 full snapshots and 55,111 numeric comparisons** across 70 scenarios. The ABI suite also checked malformed UTF-8, oversized and deeply nested input, error preservation, memory growth, per-instance isolation and event ring eviction. Hardware rendering performance and online multiplayer are separate concerns from these simulation checks. [Machine-readable receipt](../../yuga-native/docs/rust-rebuild/deep-search/classic-wasm-qa.json)
