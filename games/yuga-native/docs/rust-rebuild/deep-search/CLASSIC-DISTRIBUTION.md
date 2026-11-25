# Play classic hero sparring

[Download the classic browser game](../../../../yuga-rust/downloads/yuga-rust-classic.zip). Extract the ZIP, start a static server in the folder containing `index.html`, and open the local address in a desktop browser with WebGL 2 and WebAssembly.

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/`. Choose a hero on the normal roster and click **Hero sparring**. The HUD displays **RUST SPARRING**. Each of the 14 heroes has three abilities. The lobby also offers the existing classic bot match. The online mode connects to a separately hosted YUGA arena server. The dedicated Rust Confluence team build has its own download. [Confluence package](../../../../yuga-rust/downloads/yuga-rust-confluence.zip)

## Deploy or reproduce

The ZIP root contains `index.html`, `assets/`, controls in `PLAY.txt`, the build manifest and the Rust dependency notices. Upload the extracted contents to a static host at the site root or a subdirectory. The original PlayCanvas character and unit models load relative to the document. The HTML contains the WebAssembly module, application code, art, audio and fonts that Vite inlines. [Production Vite settings](../../../../../vite.yuga.config.ts)

From the repository root, with Node 22.12+ and Python 3 installed, run the following commands.

```sh
npm ci
python3 games/yuga-rust/tools/package_classic_web.py
python3 games/yuga-rust/tools/package_classic_web.py --check-rebuild
```

Packaging consumes the tracked classic Wasm. After changing Rust combat code, install Rust 1.88 and its `wasm32-unknown-unknown` target, then regenerate the module and its notices with `node games/yuga-rust/tools/build_classic_wasm.mjs`. [Wasm rebuild tool](../../../../yuga-rust/tools/build_classic_wasm.mjs)

The packager builds into a new temporary directory using the existing Vite production configuration, attaches the project’s notices and checks the original digests for all 14 hero rigs and seven unit models. It reopens the ZIP, instantiates the Wasm recovered from its actual contents and casts all 42 hero abilities. The build manifest records every payload member’s size and SHA-256 digest. Fixed archive ordering and timestamps allow the second command to compare an independent rebuild byte-for-byte with the first. [Packager](../../../../yuga-rust/tools/package_classic_web.py) · [Archive size, hash and checks](classic-web-package.json) · [Hero source manifest](../../../../yuga/art/hero-assets.json) · [Unit source manifest](../../../../yuga/art/unit-assets.json)

The headless native and Wasm parity tests cover simulation behavior. The graphical production test starts from extracted files on a nested HTTP path and exercises normal lobby controls. These checks use different entry points. [Rust/TypeScript comparison](classic-roster-qa.json) · [Wasm comparison](classic-wasm-qa.json) · [Verified nested-path production session](classic-production.json) · [Gameplay screenshot](classic-gameplay.png) · [Production browser smoke test](../../../../yuga/tools/smoke-classic-rust.mjs)
