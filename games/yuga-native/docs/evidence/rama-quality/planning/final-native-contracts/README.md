# Final native contract source freeze

On 2026-10-17, root authorized this final pin refresh after the Rama runtime,
art and imported-audio source freeze. This archive records the resulting pure
checks against the actual working tree and canonical hero NOTICE.

| Check | Result | Evidence |
| --- | --- | --- |
| Gameplay source pins and schema consistency | 42/42 | `source-pins.json` |
| Godot contract admission, lifecycle and replay fixtures | 242/242 | `contracts.json`, `contracts.log.txt` |
| Historical schema 1 and strict schema 2 provenance counterexamples | 118/118 | `provenance.json`, `provenance.log.txt` |
| Canonical active hero NOTICE and actual authoring files | 23 source records verified | `canonical-provenance.json` |

The catalog remains native offline content revision **4** and contains exactly
the original fourteen gameplay sources plus `rama_action_buffer.gd`. Only the
existing `player.gd` and `rama_hero_runtime.gd` digests changed. Browser and
production-proposal profiles, all wire versions, other native profile fields
and all catalog fields outside the profiles are unchanged from the archived
pre-refresh catalog.

- Final catalog SHA256: `f28949365043db23b379f68aadee4be8bfccd7c4fce5cd53322dd66882d51371`
- Native content aggregate: `8f915c1ec28ad4a322f7c6b92f976ce95a99e16c6aaf04a7e8411a6e307ee64d`
- Canonical NOTICE SHA256: `eae9e6cb3701f7030af7ec4365f6a5bd7d7d43c785e53c4f3e19f2d00981421c`
- Actual final hero GLB SHA256: `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`

`source/` contains forty exact source, metadata, fixture and NOTICE copies;
`source-manifest.json` pins their bytes. Large GLB/BLEND authoring files are
verified against the real files and recorded in `canonical-provenance.json`,
without duplicating them here. The earlier migration archive retains all old
negative checks, the original revision-3 fixtures, the failed initial descriptor
projection and the expected pre-freeze source-pin failures.

`execution.json` records the actual commands, durations and isolated temporary
XDG directories. The pure Godot run used Godot 4.6.3 headless on CPUs 0,1;
Python provenance counterexamples used CPUs 0,1. The Godot log contains no engine
error or warning diagnostics. All checked source hashes were reverified after
execution before their exact source copies were archived.

These results establish identity and pure contract behavior. They do not run
imports, exports, renders, a live transport or multiplayer match, physical GPU
performance, listening sessions or human art acceptance. Root's final gameplay
capture, full sixteen-suite quality runner and package/release checks are
separate evidence gates. This archive is not a release approval.
