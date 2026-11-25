# YUGA · Confluence in Rust

Play as **Hanuman or Rama** alongside an army fighting across three lanes. Escort troops to the enemy core. Every third wave brings cannon carts. Every fifth wave sends royal chariots into the middle lane. You can play solo or take opposing sides in a two-player room. Hanuman’s original three-guard practice is also available. [Download the game and room host](downloads/yuga-rust-confluence.zip?raw=true) · [Research, verification and roadmap](../yuga-native/docs/rust-rebuild/deep-search/README.md)

## Launch the game

**Solo.** Extract the ZIP and open `yuga-rust.html` in a desktop browser with WebAssembly and WebGL 2. Choose a hero and select **Play lane match**. To try the five attacks on stationary targets, choose **Hanuman practice**. If your browser blocks local HTML, run `python3 -m http.server 8000 --bind 127.0.0.1` in the extracted folder and open `http://127.0.0.1:8000/yuga-rust.html`.

**Two players on one computer or LAN.** The ZIP contains the same Rust match engine as a portable WebAssembly worker and bundles the WebSocket transport. Install Node **22.12 or newer** on the host computer. Both players need a browser. Run one of the following commands in the extracted folder.

```sh
# Two browser windows on the same computer
node serve_rooms.mjs

# Two computers on the same LAN
node serve_rooms.mjs --host 0.0.0.0
```

On the same computer, open `http://127.0.0.1:8787`. On the LAN, both players open the host’s LAN address on port 8787. Each chooses a hero and opens **Two-player room**. The first player selects **Create room** and shares the code. The second enters the code and selects **Join**. Keep the host running until the match ends. Leaving closes the room. The in-game menu pauses controls locally while a network match continues. The GitHub download includes the server; persistent public matchmaking remains a separate deployment.

## Controls and rules

Move with **WASD** or the arrow keys. Aim at the ground with the mouse. A shortcut casts immediately. Clicking an ability button selects it for the next click in the arena. **Esc** cancels that selection or opens the match menu.

| Input | Hanuman | Rama |
| --- | --- | --- |
| LMB | Vajra Gada strikes in front. | Kodanda draws and releases an arrow. Hold for repeated fire. |
| Q | Vajra Kavacha shields allies in front and the caster. | Piercing Dawn can strike successive enemies on its path. |
| E | Maruti Udayana vaults toward clear ground. | Measured Step moves through a short clear lane. |
| C | Lanka Dahan sweeps behind the caster and leaves a burning sector. | Guardian Circle shields and heals allies occupying its marked area. |
| X | Mountain Pulse marks a delayed impact that damages enemies and heals allies. | Dawn Volley commits to three firing lanes and releases three staggered arrows. |
| R | — | Reload the twelve-arrow magazine. An attempted primary shot on an empty magazine also starts a reload. |

Soldiers fight each other and damage the enemy core by reaching it. Hero last hits earn faction gold. The scoreboard shows core health, wave, gold and time. Both heroes can hurt the opposing human player, who respawns after three seconds. At the 18-minute limit, higher core health wins, and equal health gives a draw. Offline games enter the moving first wave 27 seconds into the same simulated clock.

## Build and test

Run these commands from the repository root with Python 3, Node 22.12+ and Rust 1.88. The build reuses the committed animation data. Godot 4.6.3 is needed to regenerate the independent native comparisons.

```sh
rustup toolchain install 1.88.0 --profile minimal --target wasm32-unknown-unknown
export RUSTUP_TOOLCHAIN=1.88.0
npm ci
cargo test --release --locked --manifest-path games/yuga-rust/Cargo.toml
python3 games/yuga-rust/tools/build_web.py
```

The packager writes `games/yuga-rust/dist/yuga-rust-confluence.zip`, the standalone HTML and a build manifest. The ZIP also contains the room host, Rust/Wasm worker, notices and launch instructions. For the optional native match executable on the host:

```sh
cargo build --release --locked --manifest-path games/yuga-rust/Cargo.toml --bin room
node games/yuga-rust/tools/serve_rooms.mjs
```

In the source checkout the default authority is the native executable. In the extracted package the host automatically finds the adjacent WebAssembly and HTML. A source host can use `--wasm PATH` to choose a portable authority. The source checkout uses its installed `ws` dependency.

```sh
cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin drill -- --map
cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin lanes -- 15 1200
cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin court -- verify
node games/yuga-rust/tools/test_room_parity.mjs
node games/yuga-rust/tools/test_rooms.mjs
node games/yuga-rust/tools/test_browser.mjs
node games/yuga-rust/tools/test_match.mjs
cargo run --release --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster -- --play sita
```

`drill` also accepts terminal commands such as `aim 0 1`, `cast 1 0 -52.5` and `wait 6`. For all fourteen classic hero kits, use the separate terminal roster lab. [Roster commands and comparisons](../yuga-native/docs/rust-rebuild/deep-search/ROSTER-PORT.md)

The army command projects an isolated wave. The court command tests the real landmark’s support and capsule clearance. Chromium, Playwright and `unzip` are required for browser tests. Tests on managed Chromium used loopback when browser policy blocked direct file navigation. [First-generation drill ZIP](downloads/yuga-rust-practice.zip?raw=true) · [Gameplay and test documentation](../yuga-native/docs/rust-rebuild/deep-search/README.md)

| Code | Responsibility |
| --- | --- |
| [Battle](src/battle.rs), [army](src/army.rs) and [world](src/world.rs) | Shared 20 Hz match, both team seats, core victory, persistent soldiers, navigation and collision. |
| [Hanuman](src/combat.rs) and [Rama](src/rama.rs) | Authoritative actions and receipts, cooldowns, projectiles, wards and published animation phase. |
| [Native host entry](src/bin/room.rs), [WebAssembly entries](src/lib.rs) and [room transport](tools/serve_rooms.mjs) | Identical Rust gameplay for native and portable room authorities. |
| [Browser input](web/main.ts), [scene](web/scene.ts) and [armies](web/army-scene.ts) | Controls and results, interpolated hero and army presentation, ability and siege warnings. |
| [Audio worklet](web/mix-worklet.js) and [Rust mixer](src/mix.rs) | Master stereo limiter adapted from the MIT OpenBF project, with a browser compressor fallback. |
