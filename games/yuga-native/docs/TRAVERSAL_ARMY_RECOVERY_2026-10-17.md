# Traversal and lane army verification handoff

This is a recovery checkpoint, not a release certificate. The cloud execution service disconnected during integration on 2026-10-17. Preserve the existing workspace and uncommitted changes. Do not recreate or reset the checkout to the older published version.

## Implemented in the workspace

- Native arena expanded from 140 × 170 m to 140 × 260 m, with eight landable decks and ten tether anchors. The original browser-authority geometry remains a separate baseline; new native geometry is offline only.
- Flight and grappling with finite energy, speed and altitude limits, collision handling, cancellation, and bounded additive rig poses.
- Three original procedural army roles: spear soldier, bow guard and banner commander. Paired waves, capped populations, delayed attacks, core outcomes and once-only player kill rewards.
- Persistent keyboard remapping, contextual help, validated settings, focus/pause input release and shared audio preferences.
- Original 20-second instrumental/electronic loop and seven pooled event cues.

## Evidence actually observed before the outage

| Check | Observed result | Limit |
| --- | --- | --- |
| Traversal physics | 34 checks passed | Later neutral-label edit rerun exited 0; refreshed report still needs reading |
| Traversal rig poses | 39 checks passed | Actual rendered review remains pending |
| Native baseline | 18 checks passed | Not a full online match |
| Controls/settings | 32 checks passed | OS-level rendered interaction review remains pending |
| Film safe settings/audio | 26 checks passed | Archived film unchanged |
| Film integration | 42 checks passed | Includes deliberate missing-model negative fixture |
| Traversal audio | 39 checks passed; eight PCM files reproduced | No human listening assessment |
| Extended map physics/UI | 27 checks passed without runtime errors | Initial failed attempt rejected; final cleanup report unread |
| Package structural security | 26 checks passed | Focused malformed-input checks, not a security certification |
| Release publication gates | 72 checks passed | Mocked publication only; no new release published |
| Army script parsing | Passed | Long simulation and integrated gameplay not verified |
| Production dependency audit | Zero reported vulnerabilities | Production dependency scope only |

## Required recovery sequence

1. Reconnect the existing workspace. Inspect Git status and preserve all feature work. Previous committed HEAD was `471d8fc98024626ca36fc6e614351bd70748dbde` on `game/yuga-native-production`.
2. Read `/tmp/yuga-world-r3/physics-ui-final*` and flow logs/reports. Confirm test counts and absence of runtime errors rather than relying on process exit alone.
3. Run the revised Python map suites. They distinguish the browser baseline from extended native geometry.
4. Check whether `tests/lane_army_cases.gd` was saved by the interrupted write. Finish the army suite and implement `tests/traversal_army_stress.gd`; neither has a confirmed passing result.
5. Stress 20 simulated minutes of paired waves; test live/corpse/attack caps, collision and separation, reset, simultaneous core outcomes, once-only gold and projectile/pulse/audio integration. Record simulation time separately from wall time and rendered performance.
6. Exercise actual platform landings, occluded anchors, energy exhaustion, pause/focus/overview cancellation and remapped controls across the combined scene.
7. Add `scripts/lane_unit_art.gd` to the package's required runtime resource list. Refresh the world manifest provenance hash and traversal controller source pins after the source freeze.
8. Implement the planned new traversal capture tools. They were not written before the outage. Capture actual frames and input/state telemetry; label scripted input and software rendering honestly. Do not present concept art as gameplay.
9. Inspect actual rendered daylight/night, minion poses, crowded lanes and small-window UI. Test the packaged Linux executable using real window input.
10. Update `TRAVERSAL_ARMY_VERIFICATION.md` with final source hashes and passed/failed/unrun gates. Only then commit, push, tag a new traversal-armies release and independently verify public downloads.

The original roadmap remains incomplete. This feature milestone does not establish commercial-game graphics parity, native competitive multiplayer, Windows execution, or analysis of proprietary game binaries.
