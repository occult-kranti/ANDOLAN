# Video access and local AI source notes

Checked 2026-10-23. The user clarified **Ollama** as the intended tool. No video source was recovered, and no PewDiePie hardware, model, or software configuration is established here.

| Supplied video | Observed result | Title / creator / transcript / timestamps |
|---|---|---|
| https://youtu.be/9W7QgI3pmT8 | Proxy CONNECT 403; curl 56; zero body bytes | All null |
| https://youtu.be/Pl7ThC4PiVA | Proxy CONNECT 403; curl 56; zero body bytes | All null |
| https://youtu.be/s9HMWYxwnOw | Proxy CONNECT 403; curl 56; zero body bytes | All null |

Each URL was requested once through the inherited HTTPS proxy with TLS verification enabled. The selected environment policy excludes YouTube; environment status reported a restricted policy with state `unknown`, so the actual CONNECT responses establish the observed failures. No alternate proxy, mirror, direct route, or third-party transcript route was used. See [video-ledger.json](video-ledger.json) and the per-video response headers and stderr under [video-probes](video-probes/). The HTTP status `000` means no origin HTTP response was received; `403` is the proxy CONNECT response.

The accessible primary sources support these distinctions:

| Component | Verified role | Practical implication |
|---|---|---|
| Ollama | Runs/manages models through a REST API; binds `127.0.0.1:11434` by default | Model inference backend; optional cloud features can be disabled with `OLLAMA_NO_CLOUD=1` and a restart. Multiple models and parallel requests consume additional RAM/VRAM. |
| Open WebUI | Self-hosted interface supporting Ollama and OpenAI-compatible APIs | Can be the chat interface connected to an Ollama server through `OLLAMA_BASE_URL`. |
| Pinokio | Script/application launcher with a terminal-like UI | Optional installer/launcher. Its scripts can execute arbitrary commands; default directories and virtual environments do not establish an enforced sandbox. |

A source-grounded local setup could connect Open WebUI to Ollama, with Pinokio optional. This is an architecture interpretation from independent project documentation, **not** a reconstruction of the blocked videos. Nothing here demonstrates a multi-agent swarm, validates local hardware capacity, or proves game reconstruction capability.

Ollama software has an MIT license. Pinokio software uses MIT license terms. Models and launched applications have their own terms. The inspected Open WebUI version includes a branding-preservation condition, with exceptions including at most 50 end users in any rolling 30-day period, prior written permission, or a qualifying enterprise license; earlier licensed materials retain those earlier terms. See the exact saved licenses rather than describing all three projects as having the same license.

All eight fetched source files returned HTTP 200 and were below 1 MiB. They are pinned to the Git HEAD observed for each official repository, and exact received-byte SHA-256 digests were verified after writing. [source-ledger.json](source-ledger.json) provides immutable URLs, commit IDs, retrieval timestamps, byte sizes, hashes, and a claim ledger with line references. Files are stored in [sources](sources/).

No software, model, browser, or game asset was installed or executed. No repository file or environment configuration was modified by this research. Further video-specific analysis needs the actual video/transcript source or a supported environment access change; no unavailable content has been filled in from guesses.

The independent [game-source notes](game-sources/README.md) preserve five successful primary-source documents and one recorded 404. QuakeJS describes a JavaScript port of ioquake3, whose documentation distinguishes released GPLv2 source from game data. Noclip describes a digital museum of game levels and documents camera/scene viewing; these documents do not establish a complete playable game reconstruction. These findings are independent of the blocked videos.
