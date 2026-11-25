# YUGA in Rust

**Play Hanuman’s Confluence drill.** Defeat the three Moon guards on the temple avenue. You have the revised 167-joint hero, five invocations, a Sun ally and the existing three-lane map. The browser handles drawing and audio. Rust WebAssembly resolves every cast, impact, shield and movement step. The guards in this drill are stationary. A separate native Rust program simulates uncontested army waves. [Download the standalone ZIP](downloads/yuga-rust-practice.zip?raw=true) · [Gameplay capture](../yuga-native/docs/rust-rebuild/browser-gameplay.png) · [Rebuild research and roadmap](../yuga-native/docs/rust-rebuild/README.md)

## Play

1. Extract the ZIP. Open `yuga-rust.html` in a desktop browser with WebGL 2 and WebAssembly. The hero, world, six audio cues and fonts are embedded.
2. If your browser restricts local HTML, run `python3 -m http.server 8000 --bind 127.0.0.1` in the extracted folder. Open `http://127.0.0.1:8000/yuga-rust.html`. This serves the file from your own computer.
3. Choose **Begin practice**. Walk with **WASD** or the arrow keys. Aim at the ground with the mouse. Use the shortcuts below to cast immediately. To cast from the action bar, select an ability, then click its target in the arena. **Esc** cancels that selection or pauses the game. The results screen lets you restart or return to the title.

| Control | Ability | What to try |
| --- | --- | --- |
| LMB | Vajra Gada | Face the nearest guard and strike within the forward arc. |
| Q | Vajra Kavacha | Face the Sun ally to shield both of you. |
| E | Maruti Udayana | Aim along clear ground and vault down the avenue. |
| C | Lanka Dahan | Put a guard behind Hanuman to catch it in the rear sweep and lingering fire. |
| X | Mountain Pulse | Choose a visible point on the floor. The marked disk damages enemies and heals allies when the delayed impact arrives. |

## Build from the repository

Use Rust 1.88, Node 22.12 or newer, npm and Python 3. The following commands start from the root of ANDOLAN. `RUSTUP_TOOLCHAIN` selects the same compiler inside the Python packaging script. Only Node dependencies from the repository lockfile are needed. The animation exporter reads the committed Godot motion library directly.

```sh
rustup toolchain install 1.88.0 --profile minimal --target wasm32-unknown-unknown
export RUSTUP_TOOLCHAIN=1.88.0
npm ci
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml
python3 games/yuga-rust/tools/build_web.py
```

The packager writes `games/yuga-rust/dist/yuga-rust.html`, a ZIP and `build.json` with the HTML, Wasm and asset digests. The distributable ZIP also includes bundled third-party notices. The published screenshot and receipt come from the package referenced at the top of this page. [Browser input and package check](../yuga-native/docs/rust-rebuild/browser-check.json)

To repeat the browser check on Linux, install Chromium or run `npx playwright install --with-deps chromium`, and have `unzip` on PATH. The driver tries a direct local file first. If the browser blocks it, the driver navigates to the same archive member over a temporary loopback HTTP server, closes the server and finishes the test offline. Use `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to select a Chromium binary explicitly.

```sh
node games/yuga-rust/tools/test_browser.mjs
```

## Run the native tools

The terminal drill takes the same inputs and advances the same simulation as the browser. Its coordinates are horizontal metres in X and Z. One tick is 50 ms. Terminal slots are numbered 1 through 5 in action-bar order. The example strikes the first guard, waits for the contact, then prints the state.

```sh
printf 'aim 0 1\ncast 1 0 -52.5\nwait 6\nstatus\nquit\n' |
  cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin drill
cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin drill -- --map
cargo run --quiet --locked --manifest-path games/yuga-rust/Cargo.toml --bin lanes -- 15 1200
```

The last command emits the census and positions for wave 15 after one minute of unobstructed movement. Godot 4.6.3 can supply a live differential check for the headless army program, plus the joint transforms for independent hero verification. [Army comparison commands](../yuga-native/docs/rust-rebuild/ARMIES.md) · [Hero check and exporter commands](../yuga-native/docs/rust-rebuild/HERO-ANIMATION.md)

## Source layout

| Path | Responsibility |
| --- | --- |
| [src/combat.rs](src/combat.rs) and [build.rs](build.rs) | Fixed-tick rules, action snapshots, health receipts and motion markers from the native data. |
| [src/world.rs](src/world.rs) | Loads the original Confluence routes and obstacles. Uses Parry for ground sweeps and sight queries. |
| [src/bin/lanes.rs](src/bin/lanes.rs) | Both factions’ formation, siege cadence, route following and isolated arrivals. |
| [src/hero.rs](src/hero.rs) | Validates the source model and replaces the five superseded actions in the exported GLB. |
| [src/lib.rs](src/lib.rs) and [web/main.ts](web/main.ts) | Native library, WebAssembly boundary, input routing, pause, audio and results. |
| [web/scene.ts](web/scene.ts) | Reuses YUGA’s PlayCanvas rendering kit, draws the source assets and samples motion against the Rust action phase. |

This checkpoint covers local training and a separate headless wave reconstruction. Competitive matches, moving combat AI, online prediction, a native graphical Rust renderer and commercial-quality art and frame times are open milestones. [Full-game migration roadmap](../yuga-native/docs/rust-rebuild/README.md)
