# Reference and reuse ledger

Version 0.4 — research executed 15 October 2026 (America/New_York).

This ledger distinguishes analysis tooling, references and code/asset imports. A root license is not an asset audit. Exact source hashes are in [source-manifest.json](research/evidence/source-manifest.json); implementation evidence belongs to the build/test report, not this research ledger.

| Material | License scope inspected | Actual disposition | Dependencies / obligations |
| --- | --- | --- | --- |
| REA 6.5.0 CLI | MIT for REA-authored code; dependencies retain their own licenses | Installed under `/workspace/tooling/rea-runtime`; source under `/workspace/tooling/rea`. Used only for static research, never bundled into ANDOLAN. | Compatible Node + procps. npm lockfile retained outside game. Root integrity/signature checks passed; complete Sigstore audit blocked by TUF 403. No persistent MCP registration. |
| Sketchbook selected controllers at `62f4b798…` | MIT copyright swift502, 2020; exact notice retained in `research/licenses/Sketchbook-MIT.txt` for research evidence | Source inspected; seven files statically analyzed. No controller implementation or assets copied to game. Original contract written from explicit observations and ANDOLAN requirements. | Source assumes Three.js 0.113.0, Cannon integration, animations and glTF seat/door metadata. These are not adopted dependencies. If code reuse is later selected, preserve full notice and audit dependency and asset rights. |
| OpenRW at `5c5f266…` | GPLv3-or-later program; README separately lists FFmpeg, Bullet and SDL licenses | README/license reference only. No code adopted. | Original GTA III PC data required to run; not requested or acquired. Any future linked/adapted code needs a deliberate GPL-compatible distribution plan. |
| OpenLara at `3b268ca…` | BSD-2-Clause engine notice | README/license reference only; browser portability is documented, not tested | Attribution obligations apply to code reuse. Original-game assets are outside the engine license assumption. |
| OpenGOAL at `b6c8430…` | ISC project license | README/license reconstruction-method reference only. No decompiled game code adopted. | Legitimate PS2 game data required. Toolchain and game-data scope differ; per-file review required before reuse. |
| GTA / Watch Dogs / Minecraft / HITMAN / Ghost of Tsushima | No license to code/assets established by this review | General design influences only | No source/binaries/assets imported. No proprietary runtime measurements claimed. |
| Supplied ANDOLAN handoff | User-supplied creative brief; third-party entries remain references | Original city, cast and mission direction used by the implementation team | Attached prompt is a design input; runtime claims must be verified separately. Research claims retain their original uncertainty. |
| ANDOLAN generated geometry and UI | Authored in this repository for this project | Original product work | No borrowed character likenesses, commercial game logos, music or branded city assets are required. Final shipped asset inventory must follow actual files. |
| PlayCanvas, Rapier, Colyseus and development dependencies | Candidate licenses in supplied plan are not enough to pin actual versions | See root package manifests/lockfile for actual selected runtime versions; this research pass does not substitute proposed versions for installed ones | Preserve dependency license notices for shipped distributions; test the chosen versions together. |

## Screened source files

All below are from `swift502/Sketchbook@62f4b7986fd1ce1e4f91daba89ef032c20a6ce55`. Full SHA-256 values are retained in the manifest.

- `src/ts/characters/Character.ts`: selection, control transfer and occupant assignment.
- `src/ts/characters/VehicleEntryInstance.ts`: approach-to-entry gate.
- `src/ts/characters/character_states/vehicles/EnteringVehicle.ts`: physics/parenting and transition.
- `src/ts/characters/character_states/vehicles/Driving.ts`: driving-state ownership handoff.
- `src/ts/characters/character_states/vehicles/ExitingVehicle.ts`: animation and next-state branches.
- `src/ts/characters/character_states/vehicles/ExitingStateBase.ts`: detach/physics restoration.
- `src/ts/vehicles/VehicleSeat.ts`: scene metadata and local occupancy field.

The REA evidence excerpts contain identifiers and literal source facts, so the MIT research notices accompany them. The full 8.7 MB evidence record remains outside the product checkout; the compact summary and 8 KB focused trace are committed research artifacts. No large third-party asset directory is placed in the game.

## Adoption rule

Before copying any new component, record upstream URL and immutable revision, exact files, per-file license and notices, third-party dependencies, asset rights, modifications, product destination and executed verification. For an idea-only adaptation, label its values **original design** and avoid implying behavioral equivalence. Runtime tests and license review are separate evidence.
