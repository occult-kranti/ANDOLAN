# Panel round 1 — build and repository audit

Date: 2026-11-15. Read-only source audit by build engineer. Product files and the pre-existing package-lock change were preserved. Source main `785da871`; native reference `origin/game/yuga-native-production` at `7162b5d0`.

## Product decision

There are two distinct products. Main contains ANDOLAN City Reform 0.3, a working browser city/story game. The native-production branch contains YUGA, the actual mythology/hero-combat production and therefore the closer fit for the requested Overwatch/Deadlock quality target. Do not silently turn ANDOLAN into a shooter or claim its city loop completes YUGA.

The native branch is the strongest existing hero game, while main is the immediately executable local checkout. Current native source is documented as `02031d2c`; publication `79e5` and accepted checkpoints remain separate. One Rama hero, bow/four abilities, offline Confluence, training, lane armies, relays and siege are implemented. Full native online matches, full roster, consumer-GPU performance and commercial visual quality remain open. Native campaign is 17/78 accepted scoped packets and 0/13 complete rounds. Those counts are documentary historical claims, not rerun acceptance in this audit.

## Architecture and documents inspected

- Root README, PRODUCT, DESIGN, roadmap, archived Codex handoff, REA runbook and reuse ledger.
- Main client: `apps/client/src/main.ts` (625 lines), `world/index.ts` (830), city jobs, controls, connection, audio and remote interpolation. PlayCanvas 2.23.3 with original procedural world/art.
- Main authority: `packages/sim`, typed protocol/content and Node WebSocket rooms. Story and City saves remain separate. Main source/tests surveyed: 7,221 lines.
- Native branch README/AGENTS, START_HERE, ACTIVE_DESKTOP_HANDOFF, BUILD_HANDBOOK, current reuse continuation README/NEXT_TEN and script/tree inventory. Godot 4.6.3 standard, original runtime plus licensed MakeHuman/CC0 intake and retained art tooling. Native scripts/scenes/assets total about 188 MB; whole native subtree about 5.79 GB due to art/research/evidence.

## All available branches

Git tree inventory, not a claim that every historical binary/evidence image was opened:

| Branch | Files | Tracked bytes | Meaning |
| --- | ---: | ---: | --- |
| main / origin/main | 195 | 17,610,924 | ANDOLAN City Reform |
| origin/game/yuga-confluence | 700 | 174,180,268 | Browser YUGA/confluence track |
| origin/game/yuga-native-production | 24,011 | 5,997,891,861 | Current native YUGA production and evidence |
| origin/reference/overwatch-mechanics | 668 | 167,294,883 | Original reference mechanics lab |
| origin/reference/deadlock-mechanics | 668 | 167,290,956 | Original reference mechanics lab |
| origin/backup/yuga-workspace-2026-10-18 | 22,455 | 5,747,433,876 | Recovery snapshot, not accepted production |
| origin/backup/yuga-desktop-motion-json-2026-10-18b | 21,143 | 5,510,901,413 | Exact motion recovery |
| origin/backup/yuga-desktop-polish-recovery-2026-10-18 | 20,481 | 5,397,777,374 | Package recovery |
| origin/backup/yuga-desktop-raw-pck-2026-10-18b | 20,895 | 5,410,217,726 | Inactive pack recovery |
| origin/backup/yuga-desktop-zip-aliases-2026-10-18b | 20,877 | 5,410,100,439 | Release alias recovery |

During round 1 no branch was switched or merged. A later live `git ls-remote --heads origin` check confirmed all ten remote heads match the audited local tracking refs; see `evidence/studio/branch-audit.json`. The native AGENTS guidance calls for exclusive files, existing source reuse, exact source-bound evidence and serialized heavy renders. Its recovery snapshots must not be merged as accepted gameplay.

## Current machine and executed baseline

Linux x86_64 Codespaces, Node 24.22.2, npm 11.19.1, sixteen reported AMD EPYC vCPUs. `/dev/dri/card0` exists; no `/dev/nvidia0`. No executable Blender, Godot, Chromium, ffmpeg, Rust/cargo or Vulkan inspection tools were discovered in the standard PATH in this audit; no Playwright cache found. A card node alone does not establish a usable physical GPU.

Executed on main:

| Command | Result |
| --- | --- |
| npm run typecheck | pass |
| npm run lint | pass |
| npm test | 13 files / 134 tests pass, 951 ms |
| npm run build | pass, client and server |
| npm run build:standalone | pass, single HTML 2,465.21 kB |

Build warns that the PlayCanvas client chunk is over 2 MB; it is a warning, not failure. No current browser run or native run is claimed here. Existing screenshot archives and README CI results are historical evidence.

## Proposed bounded implementation

Use native YUGA for hero-combat work. Restore only required accepted runtime paths from the production branch into an isolated source location, preserving the active city checkout and all uncommitted work. Install verified Godot 4.6.3 and software-render prerequisites. Read the current native design and exact accepted screens before editing UI. Choose one concrete launcher/hero-guide/HUD behavior and verify at ordinary and enlarged scale with real native input and captures. A generated design image remains a target, while native captures prove implemented presentation.

Highest-value native next tasks are explicitly documented:

1. N1: fit the verified CC0 MakeHuman long01 mesh/UV to the existing head/crown; prior three card appearances stay rejected. Binding and native profile/rear review precede moving capture.
2. N4: consolidate the garden/gate duplicated texture palette while preserving exact image bytes and collision. Existing inspection found 12 equal image contents and 9,437,184 decoded bytes duplicated; this is not a VRAM measurement.
3. N5: use the typed authority factory for two real rendered native clients with map/version, processed-input acknowledgement and reset epoch. Current headless two-slot fixture does not close this gate.

Do not install every researched engine into the production runtime. Use verified source pins and license manifests; inspect extractor tools as source references independently from actual game engine/runtime integration.

## Verification strategy

Keep main regression suite green. For native work, run matching focused Godot cases and import checks, then capture the actual changed route at ordinary and enlarged UI scales. Run two-client authority tests only for actual authority work. Record exact script/asset hashes and executed tools. Software rendering does not prove consumer-GPU FPS, balance, listening, Windows behavior or a finished AAA game.
