# Reference investigation — ANDOLAN

Research session: 15 October 2026, America/New_York (16 October UTC). This review used the supplied v0.3 plan as a design input. Uploaded instructions were not treated as authority to register integrations or override the user's actual request.

**Result:** REA 6.5.0 ran a real static analysis of seven MIT-licensed Sketchbook controller files. Source inspection produced an original vehicle-transition contract. No GTA, Tomb Raider, Jak, or Sketchbook gameplay was executed; no proprietary game data was acquired; no external game code was imported into the product. REA did not produce a playable reconstruction.

## Evidence vocabulary

- **Observed:** a command, file, or result actually inspected in this session. Source observations are explicitly distinguished from runtime observations.
- **Documented:** the pinned upstream documentation makes the claim; we did not reproduce it.
- **Inferred:** an interpretation of the available source, bounded by the files inspected.
- **Original design:** a proposed ANDOLAN behavior, not a recovered mechanic.
- **Unknown:** unavailable or untested evidence.

Exact URLs, file hashes and byte counts are in [source-manifest.json](research/evidence/source-manifest.json). Current HEAD hashes were resolved using HTTPS `git ls-remote`; REA and Sketchbook were then cloned outside the product checkout. The source trees remained clean. A commit hash identifies source; it is not a signature or proof of all upstream claims.

## Pinned projects

| Project | Inspected revision | Evidence and intended use | Boundary |
| --- | --- | --- | --- |
| [REA](https://github.com/morluto/rea/tree/d52a488476e7c41f573f23a1965d3f32d4e6a7f2) | `d52a488476e7c41f573f23a1965d3f32d4e6a7f2` | Observed README, CLI/workflow docs, manifests and selected source. Ran npm `rea-agents@6.5.0` locally. MIT analysis toolkit. | The npm package and source tree both report 6.5.0; byte-for-byte source-to-package equivalence was not established. |
| [Sketchbook](https://github.com/swift502/Sketchbook/tree/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55) | `62f4b7986fd1ce1e4f91daba89ef032c20a6ce55` | Observed MIT license, controller source and seven-file REA analysis. Closest technical reference for walk/drive transitions. | README states final update/archiving on 20 February 2023. Its Three.js 0.113.0 and TypeScript 3.9-era stack is not the product stack. Assets not adopted. |
| [OpenRW](https://github.com/rwengine/openrw/tree/5c5f266b71aa55aeec8cb4d823f19e7c4348f3bd) | `5c5f266b71aa55aeec8cb4d823f19e7c4348f3bd` | Observed README and COPYING; documented GTA III executable reimplementation, GPLv3-or-later. | Requires a legitimate original PC game. No runtime, code import, GTA V support or browser port established here. |
| [OpenLara](https://github.com/XProger/OpenLara/tree/3b268ca4bf986c380f44a26ffd9218bf6d376249) | `3b268ca4bf986c380f44a26ffd9218bf6d376249` | Observed README and BSD-2-Clause license; README links a WebGL demo. | Browser target is documented, not run here. Engine license does not establish rights to Tomb Raider data. |
| [OpenGOAL](https://github.com/open-goal/jak-project/tree/b6c8430c0b0a5cb139b939bcf0ffd25285b896c7) | `b6c8430c0b0a5cb139b939bcf0ffd25285b896c7` | Observed README and ISC license. Documents decompile → type/cast correction → GOAL recompile → native x86-64 runtime, with reconstruction tests. | Requires legitimately obtained PS2 game data. No game assets included upstream; no arbitrary PS2-to-browser conversion claimed. Runtime and test claims not rerun. |

## How REA is being used

The pinned README describes one toolkit for native binaries, JavaScript/Electron, .NET, Android and other specialized domains. Native providers and mobile tools have separate requirements. The current JavaScript lane needs Node 22.19+, 24.11+, or 26+ and, on Linux, procps-compatible `ps`. This environment supplied Node 24.19.0, npm 11.9.0 and procps-ng 4.0.4. No native analysis engine was necessary for this source question.

The pinned [DX-Ball case-study source](https://github.com/morluto/rea/blob/d52a488476e7c41f573f23a1965d3f32d4e6a7f2/website/public/showcase/dx-ball/index.html) documents a useful pattern: inspect a small function, challenge the first pseudocode interpretation using instructions and callers, reconstruct C, then compare against the original. Its 7 October checkpoint reports 55 maintained C functions, 45,380 original-code comparisons and 33 functions with matching bytes; the highlighted sound-panning function reports 3,205 comparisons and a 63-byte compiler match. **These remain upstream reports.** We inspected the repository's case-study page source, not its native executable or oracle runs. The same page says playable-game work continues. That is evidence for narrow behavior reconstruction, not automatic finished-game production.

For ANDOLAN the question was: **which state, ownership, physics and input boundaries appear when a character enters and leaves a car?** Direct source was available, so binary decompilation would add no necessary evidence. REA inventoried the source, emitted immutable evidence identities, and located occupancy-related syntax. Manual source reading supplied the control-flow interpretation. [VEHICLE_TRANSITION_SPEC.md](research/VEHICLE_TRANSITION_SPEC.md) states the resulting original multiplayer contract.

### Actual run

| Check | Observed result |
| --- | --- |
| Local install | `rea-agents@6.5.0`, 173 packages, lifecycle scripts disabled; CLI `--version` returned 6.5.0. No global or persistent agent/MCP integration. |
| Package identity | Root tarball 5,634,033 bytes; SHA-512 matches registry metadata and installed lockfile. Both published registry signature entries verified with the registry public key. |
| Broader provenance audit | `npm audit signatures` stopped on HTTP 403 fetching Sigstore TUF metadata. Full dependency/provenance verification was not completed. TLS and npm integrity checks stayed enabled. |
| Static application analysis | Exit 0. Seven selected source files, 40,667 text bytes, 6,410 AST nodes, 153 findings, zero parse failures. |
| Coverage | Explicitly partial: 184 inventoried files unselected. The semantic graph has 3,372 nodes, 1,759 relations, 3,516 unknowns. These are analyzer counts, not passed tests. |
| Occupancy trace | Exit 0; property `occupiedBy`, backward provenance: one seed, one node, zero traversed relations, one relevant unknown. Status **ambiguous**, coverage **partial**. |
| Source runtime | No reference application was executed. Animation duration, driving feel, collision behavior, controller support and multiplayer capacity remain unobserved. |

The occupancy trace is a useful limit: REA retained an exact source identity and location, but did not resolve an end-to-end seat-ownership proof. It would be misleading to call the trace a recovered multiplayer algorithm. For these small readable files, source inspection was more directly useful; REA adds repeatable inventory, identities and explicit uncertainty. Keep it an optional research tool, outside the game runtime and build dependency graph.

### Source findings that changed the implementation contract

1. **Observed source:** `EnteringVehicle.ts:43–47` resets velocity, disables character physics and attaches the existing character to the vehicle. After animation completion, lines 66–80 occupy a seat and switch to driving or sitting. This motivates one stable actor identity, with authority separate from visual attachment.
2. **Observed source:** `Character.ts:775–787` assigns/clears the local seat occupant and character seat reference. Those methods do not arbitrate simultaneous remote requests. **Original design:** ANDOLAN's server must serialize claims and preserve both sides of the relationship atomically.
3. **Observed source:** `Character.ts:703–718` transfers controls; lines 746–755 clear vehicle controls on exit. **Original design:** reset held movement state when switching control context and on blur/disconnect, so a stale throttle does not survive exit.
4. **Observed source:** `ExitingStateBase.ts:40–50` detaches the existing actor, restores physics and copies chassis velocity. **Original design:** first slice restricts exit to a nearly stopped car and chooses a validated clear exit position; moving stunt exits can be designed later.
5. **Observed source:** entry and exit animation placement depend on scene metadata (seat, entry point and optional door objects). **Inferred:** copying the class alone would not create working movement; compatible assets and metadata would also be required. We choose original meshes and scene data.

## Remaining scope

Standalone JVM/JAR analysis was not exercised. Current REA Android documentation specifies a full JDK 17+ and pinned `jadx-headless-mcp 0.7.1` for APK analysis; that is not evidence that an arbitrary Minecraft JAR is supported. The handoff's Java issue claim has not been revalidated through a live issue page, so it is not carried forward as a current unresolved-feature assertion.

GTA/Online, Watch Dogs 2, Minecraft, HITMAN and Ghost of Tsushima remain design inspirations supplied by the handoff. No proprietary code, timing values, levels, UI, dialogue, art or audio were copied or claimed as independently measured here. This pass intentionally studies one applicable controller question rather than every reference title.

For a future binary study, first record an authorized target, exact version/hash, observation method and a question that readable source cannot answer. Provider setup, native execution and licensed data are separate prerequisites. None blocks the original browser implementation now.
