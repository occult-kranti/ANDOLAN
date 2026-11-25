# YUGA · Confluence in Rust

**Optional Hanuman sculpt preview.** A [separate tested download](downloads/yuga-rust-hanuman-sculpt-preview.zip?raw=true) uses a subtle facial-geometry candidate. The standard download below still uses the prior model. The preview's [build, visual and rig evidence](../yuga-native/art/hanuman-build-qa-2026/README.md) records its limits.

The latest branch package includes a camera-clearance solver, a corrected interrupted vault, elevation-aware Hanuman area attacks and a timed Mountain Pulse visual. The camera solver checks the authoritative building and deck boxes; animated weapons and tail can still need framing work. The in-game rock is an interim cue, and the richer [five-action Blender study](../yuga-native/art/hanuman-motion-panel-2026/README.md) is an offline production study. [Panel results and next steps](../yuga-native/docs/design/five-round-panel-2026/README.md)

**Classic hero sparring.** A second download runs all fourteen heroes’ original weapons and 42 abilities through Rust and WebAssembly in Sangam City. Extract it, serve the folder with `python3 -m http.server 8000`, open `http://localhost:8000`, select a hero and choose **Hero sparring**. [Download the graphical roster](downloads/yuga-rust-classic.zip?raw=true) · [Screenshots, controls and build](../yuga-native/docs/rust-rebuild/deep-search/CLASSIC-DISTRIBUTION.md)

Play as **Hanuman or Rama** in a private hero-only match: five against five, three against three, or one against one. Explore the existing arena alone or try Hanuman’s three stationary practice targets. Soldier waves are paused; their existing code and visual assets are preserved for possible reuse. [Download the game and room host](downloads/yuga-rust-confluence.zip?raw=true) · [Proposed 5v5 map, match script and next steps](../yuga-native/docs/design/mandala-rift-5v5/README.md)

## Launch the game

**Solo.** Extract the ZIP and open `yuga-rust.html` in a desktop browser with WebAssembly and WebGL 2. Choose a hero and select **Explore arena**. Exploration has no AI opponents. To try the five attacks on stationary targets, choose **Hanuman practice**. If your browser blocks local HTML, run `python3 -m http.server 8000 --bind 127.0.0.1` in the extracted folder and open `http://127.0.0.1:8000/yuga-rust.html`.

**Hanuman.** Click **Mountain Pulse** in the action bar and point at the ground. The seven-metre ring previews its footprint. A gold center marks a clear landing, and a cross explains a blocked or distant target in the status line. Press **X** for an immediate cast, or **Esc** to cancel an armed shot. In practice, the technique counter credits effective casts. [Hero art, timing and testing](../yuga-native/art/hanuman-hero-finish/GAMEPLAY.md)

**Private 5v5, 3v3 or 1v1, on one computer or LAN.** The ZIP contains the same Rust match engine as a portable WebAssembly worker and bundles the WebSocket transport. Install Node **22.12 or newer** on the host computer. Each player needs a browser. Run one of the following commands in the extracted folder.

```sh
# Browser windows on the same computer
node serve_rooms.mjs

# Computers on the same LAN
node serve_rooms.mjs --host 0.0.0.0
```

On the same computer, open `http://127.0.0.1:8787`. On the LAN, players open the host’s LAN address on port 8787. Each chooses a hero and opens the private room controls. The host selects **5v5 teams**, **3v3 teams** or **1v1 duel**, clicks **Create room** and shares the code. The remaining players enter that code and select **Join**. The match starts when all ten, six or two seats are filled. Keep the host running until the match ends. Leaving closes the room. The in-game menu pauses controls locally while a network match continues. The GitHub download includes the server; public matchmaking, internet hosting, reconnection and production-scale security remain separate work.

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

The current interim mode awards a point to the opposing team for each hero knockout. The target is 25 in 5v5, 20 in 3v3 and 10 in 1v1; eliminated heroes respawn after three seconds. A simultaneous tie at the target continues until a team leads. At the 18-minute limit, the higher score wins and a tie is a draw. There are no lane waves or autonomous jungle units. This is not yet the proposed [round-based two-site objective mode](../yuga-native/docs/design/mandala-rift-5v5/MATCH_SCRIPT.md), and Mandala Rift is not yet the playable map.

## Build and test

Run these commands from the repository root with Python 3, Node 22.12+ and Rust 1.88. The build reuses the committed animation data. Godot 4.6.3 is needed to regenerate the independent native comparisons.

```sh
rustup toolchain install 1.88.0 --profile minimal --target wasm32-unknown-unknown
export RUSTUP_TOOLCHAIN=1.88.0
npm ci
cargo test --release --locked --manifest-path games/yuga-rust/Cargo.toml
python3 games/yuga-rust/tools/build_web.py
```

For a reviewed experimental GLB without replacing the standard model, add `--hanuman-model path/to/hero.glb` and use a separate `--output` directory. The packager checks for a skin and required gameplay clips and records the embedded model's hash; perform visual and motion review separately.

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
node games/yuga-rust/tools/test_5v5_rooms.mjs path/to/extracted-package report.json
node games/yuga-rust/tools/test_5v5_browser.mjs path/to/extracted-package report.json gameplay.png
cargo run --release --locked --manifest-path games/yuga-rust/Cargo.toml --bin roster -- --play sita
```

`drill` also accepts terminal commands such as `aim 0 1`, `cast 1 0 -52.5` and `wait 6`. For all fourteen classic hero kits, use the separate terminal roster lab. [Roster commands and comparisons](../yuga-native/docs/rust-rebuild/deep-search/ROSTER-PORT.md)

The army command projects an isolated historical wave and does not enable waves in hero-only matches. The court command tests the real landmark’s support and capsule clearance. Chromium, Playwright and `unzip` are required for browser tests. Tests on managed Chromium used loopback when browser policy blocked direct file navigation. [First-generation drill ZIP](downloads/yuga-rust-practice.zip?raw=true) · [Historical six-seat tests and gameplay capture](../yuga-native/docs/rust-rebuild/deep-search/SQUADS.md) · [Gameplay and test documentation](../yuga-native/docs/rust-rebuild/deep-search/README.md)

| Code | Responsibility |
| --- | --- |
| [Battle](src/battle.rs), [army](src/army.rs) and [world](src/world.rs) | Shared 20 Hz hero skirmish, team scoring, navigation and collision; historical wave simulation is retained but disabled in current matches. |
| [Hanuman](src/combat.rs) and [Rama](src/rama.rs) | Authoritative actions and receipts, cooldowns, projectiles, wards and published animation phase. |
| [Native host entry](src/bin/room.rs), [WebAssembly entries](src/lib.rs) and [room transport](tools/serve_rooms.mjs) | Identical Rust gameplay for native and portable room authorities. |
| [Browser input](web/main.ts), [scene](web/scene.ts) and [armies](web/army-scene.ts) | Controls and results, interpolated hero presentation, plus retained army presentation for older modes. |
| [Audio worklet](web/mix-worklet.js) and [Rust mixer](src/mix.rs) | Master stereo limiter adapted from the MIT OpenBF project, with a browser compressor fallback. |
