# Production guide and native systems milestone

17 October 2026. This source milestone completes the full-game planning baseline
and advances bounded systems work. It does not replace the published training
preview with a finished online game.

## Guide and stack

- [Game design](GAME_DESIGN_MASTER.md): fourteen heroes, forty-two abilities,
  complete player journey, objectives, economy, world, animation and sound.
- [Production roadmap](FULL_GAME_PRODUCTION_ROADMAP.md) and
  [dependency ledger](ROADMAP_BACKLOG.json): sixteen gates and seventy owned
  tasks, including current versus proposed rules and evidence requirements.
- [Independent review](PRODUCTION_GUIDE_REVIEW.md): corrected roster/dependency
  mismatches, coordinate/elevation gaps, simultaneous outcome semantics and
  unsupported completion claims. Accepted as production guidance.
- [Research desk](RESEARCH_ENGINEERING_DESK.md): five actual requests with
  bounded source, implementation, countercheck and handoff stages. The
  [BRUTAL decision](research/BRUTAL_STACK_DECISION.md) retains Godot/Blender;
  a custom engine requires a measured reason and the missing production systems.

## Implemented and checked

The authority now preserves the final fractional projectile travel interval.
Seven of nine new cases failed on the old behavior; all nine pass after the
repair, and the full rules suite passes 225 tests with a passing typecheck.
[Exact evidence](research/projectile-lifetime-evidence.json) retains source,
test and report hashes. Shared sampled-radius collision still differs from the
native swept ray; this repair does not establish complete collision parity.

The [native transport](NATIVE_NETWORK_ADAPTER.md) and
[interpolator](NATIVE_INTERPOLATION.md) were reconstructed after a cloud-worker
replacement. Fresh two-client tests cover identity, input, reconnect, commands,
finish, cleanup and malformed numeric snapshots. Twenty-seven deterministic
checks, recorded replay and six deliberately defective variants exercise the
smoothing limits. Exact reports and recordings are in
[native-network-final](../tests/evidence/native-network-final/manifest.json).
These are headless loopback clients, not rendered multiplayer or WAN evidence.

The licensed carry library was reconstructed without replacing the original
clips. Thirty-five numerical checks and an actual
[236-frame motion review](evidence/motion-carry-restored/README.md) now exist.
All 21 inferred support samples place the lower sole within 5.0012 mm of the
floor, while simultaneous flight peaks at 221.906 mm. The open grip, rigid
carry and unresolved moving-ground contact keep runtime promotion open.
Numerical success does not override those visual findings.

Restored native gameplay passes 18 checks and seven projectile regressions.
Both custom asset validators pass. Independent Khronos validation reports no
format errors in either current GLB; Rama's non-root skinned-mesh warning is
retained. Twelve roadmap cases exercise valid completion, dependency cycles,
premature closure, blocked ready queues and missing/stale evidence. Linux and
Windows resource packs export and pass pack inspection; Windows execution and
physical GPU performance remain unverified.

## Reusable environment

The tested setup entry point is `bash tools/cloud/setup-native.sh` from the
repository root. It uses the prepared Godot 4.6.3 standard installation, locked
Node dependencies, project import, relevant rules/native checks and a verified
task-local Debian 13 Xvfb/Mesa runtime. The renderer installer preserves TLS and
checks exact package byte counts and SHA-256 values. No vendor runtime is added
to the source tree. The arena entry point was started and `/health` verified
protocol 2, 20 Hz simulation and 10 Hz snapshots before clean shutdown.

For later sessions, inspect the existing checkout and preserve its changes;
do not create a worktree or reset the branch automatically. Services must be
started again when needed. The current cloud worker has no physical GPU;
software-rendered captures establish pixels and motion samples, not target-PC
frame rates. Run one heavy software renderer at a time.

The worker replacement lost later uncommitted hero/world corrections. Current
assets are restored published Rama `6657f4bf…` and courtyard `1454e036…`.
Those later art corrections require reproduction and fresh captures. Their
historical acceptance is not evidence for files that are absent.

## Next dependency gates

Use the ledger's dependency-ready `next_packets`: version the rules/map/replay
contracts, complete the source registry and resolve the open animation/art
packets. Then implement the entity/aim/elevation bridge and a rendered native
match. Production hero quality, all fourteen native kits, full city, operated
multiplayer, platform execution and launch qualification remain open.
