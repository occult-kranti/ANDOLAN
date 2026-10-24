# Reuse and rights

This project-local adapter does not assert a repository-wide license. Existing
YUGA sources retain their original rights. The final execution receipt hashes the
actual sources reused; no new upstream game source or assets were downloaded.

| Existing source | Actual reuse | Rights/source boundary |
| --- | --- | --- |
| `games/yuga/server/server.ts` and `clock.ts` | Public parser, transport, identities, sessions, room lifecycle and snapshot scheduling; scratch copy replaces four import bindings | Existing project source; no new blanket license inferred |
| `games/yuga/shared/simulation.ts`, `types.ts`, `heroes.ts`, `map.ts` | Existing actor/input/schema dependencies; superclass planar match step disabled | Existing project source; old browser map remains planar |
| `games/yuga-native/scripts/arena_client.gd` and `arena_interpolator.gd` | Exact scratch copies used by both real native clients | Existing project source; no geometry or art copied |
| `games/yuga-native/scripts/player.gd` | Bounded capsule movement core adapted to explicit server inputs | Existing project source; other player/hero/traversal/render logic is not reproduced |
| `games/yuga-native/tests/physics_authority_cases.gd` and `assets/contracts/physics-fixture-v1.json` | Existing fixture construction and exact collider contract | Existing project fixture, not a production map or imported commercial level |
| Godot 4.6.3 stable official `7d41c59c4` | Executed headless native physics, TCP and WebSocket clients | MIT; existing `NOTICE/GODOT-LICENSE.txt`; separately installed executable, not vendored here |
| `ws` 8.22.0 and `tsx` 4.23.15 | Existing locked Node dependency/runtime | MIT; original installed package notices remain authoritative; no lockfile changes |
| Node 24.19.0 locally; CI Node 22 required at least 22.12 | Existing runtime and built-in TCP/process tools | Node and bundled dependencies retain upstream notices; no model inference occurs |

The contract, narrow authority subclass, private TCP adapter, staged input driver,
validation and runner are project-local work. No Deadlock, Dota 2, Overwatch or
TF2 binary, map, art, character, texture or animation is copied or analyzed here.
REA/Ghidra is not exercised by this transport/physics experiment. No full engine
clone, commercial asset extraction or GPU access occurs.
