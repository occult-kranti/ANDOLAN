# Primary game project sources

Fetched 2026-10-23 through the inherited HTTPS proxy with TLS verification. Every response was limited to 1 MiB, and saved body lengths and SHA-256 hashes were reverified. No project was installed or executed. The URLs name moving branches; the retained bytes and hashes identify the inspected snapshots.

## Findings

- **QuakeJS:** Its README line 3 calls it a JavaScript port of ioquake3 using Emscripten. This is a source-port example, not evidence of reconstructing a game solely from a compiled binary.
- **Released source and assets:** ioquake3 README lines 46–48 refer to the Q3 source release; lines 90–99 state that Quake 3 game source is GPLv2 and game data remains separate. Do not extend source-code permission to all game content.
- **Noclip:** `src/index.html` line 7 describes a “digital museum of video game levels.” README line 5 credits model-format reverse engineering, and lines 42–67 document camera and scene controls. These support the game-level viewer category. They do not establish complete playable reconstruction of every represented game.

The attempted root-level noclip `index.html` returned 404; the source-backed path is `src/index.html`. That failed response is retained in the ledger and is not used as claim evidence.

## Source snapshots

| Source | HTTP | Bytes | SHA-256 |
|---|---:|---:|---|
| [ioquake3-readme](https://raw.githubusercontent.com/ioquake/ioq3/main/README.md) | 200 | 29860 | `bedca869dd8ca41c6368037c749f86c90f403e66129db94ba0265c9eba97661a` |
| [noclip-index](https://raw.githubusercontent.com/magcius/noclip.website/master/index.html) | 404 | 14 | `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed` |
| [noclip-package](https://raw.githubusercontent.com/magcius/noclip.website/master/package.json) | 200 | 4681 | `d5d591f9bbee6940e7eca2955103bf7b4e2364ab0e242d64675a56da79513c8d` |
| [noclip-readme](https://raw.githubusercontent.com/magcius/noclip.website/master/README.md) | 200 | 4244 | `4b8a5a1be6dde9847f75350acfe357789f076b2878815dc5a46e6aa5bcf0db7b` |
| [noclip-src-index](https://raw.githubusercontent.com/magcius/noclip.website/master/src/index.html) | 200 | 734 | `24b15f8dfcd3c2aba4628ed4aa9d533d01be6b8b46011807e8d74ea19b49fc4a` |
| [quakejs-readme](https://raw.githubusercontent.com/inolen/quakejs/master/README.md) | 200 | 4505 | `3406443b5683021eb5d4ec5da8ddcc63003cde7e93cc91dac40637ff8d704461` |

`source-ledger.json` records exact URLs, fetch times, HTTP responses, bytes, hashes, TLS results and local filenames. `claims.json` maps claims to source line ranges. Per-source JSON and response headers are also retained.
