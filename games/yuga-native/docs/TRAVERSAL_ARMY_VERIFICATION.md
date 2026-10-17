# Longer lanes, traversal and army verification

Release status: integration in progress. Only a completed report tied to current source establishes a passing gate. Earlier pre-outage results in `TRAVERSAL_ARMY_RECOVERY_2026-10-17.md` are historical, not the acceptance evidence for recovered source.

## Design contract

The native Confluence field grows from 140 × 170 m to 140 × 260 m: 53% more longitudinal space. Three routes retain distinct silhouettes and readable intersections. Eight original browser blocker footprints are preserved; eight native landing platforms, longer routes, spawns and objectives are explicitly separate from browser authority. This milestone is local practice, not native online multiplayer.

Sun/Moon teams have spear soldiers, bow guards and banner commanders. Roles are identified by weapon, shape and minimap symbols, not color alone. Paired waves advance along three routes, attack enemies, damage cores and allow reset. Once-only last-hit rewards prevent repeated corpse farming. Longer travel time makes forward staging and elevated routes meaningful, but competitive balance still requires human matches.

Flight and tether traversal use finite energy, cooldowns, line of sight and capsule collision. Actual `CharacterBody3D.move_and_slide` moves the hero; the rope is a visual aid. A 24 m feet ceiling, 36 m tether range and speed caps bound the movement. Rings identify traversal opportunities; solid decks identify safe landings. Vayu lift and Naga tether are invented game relics, not scriptural claims.

## Three review rounds

1. **Design and contracts:** gameplay, movement, world, UI and audio owners agree on shared APIs, lane geometry, bounded resources and acceptance tests. Selected official Godot docs and Game Programming Patterns passages inform implementation; retained player feedback informs attention, help and lifecycle priorities.
2. **Adversarial implementation review:** owners exercise malformed settings/configuration, collision boundaries, input release, caps, reset, pool overflow and exact reward semantics. An independent reviewer tests the combined scene and packaging rather than treating owner summaries as proof.
3. **Release review:** freeze source; capture the actual renderer; inspect small-window controls and motion; validate exported PCK contents, notices and hashes; execute the portable Linux build; publish only after mandatory CI gates and remote byte verification. Windows execution and hardware-GPU performance are separate qualification work.

## Required gates and repeatable commands

Run from repository root with Godot 4.6.3 after `godot --headless --path games/yuga-native --editor --import --quit`. Set reports to a new directory; retain failures. The command pattern for GDScript suites is:

```sh
godot --headless --path games/yuga-native --fixed-fps 60 \
  --script res://tests/traversal_cases.gd -- --report=/tmp/NEW/traversal.json
```

| Gate | Suite/tool | Required observation |
| --- | --- | --- |
| World specification | `world_map_cases.py`, `world_plan_cases.py` | Baseline/native scope separation, route clearance, bounds, platforms and rejection fixtures |
| Physical traversal | `traversal_cases.gd`, `world_scene_cases.gd` | Finite motion, real thin-wall/ceiling collision, landing and bounds, LOS, energy/cooldown cancellation |
| Rig poses | `traversal_pose_cases.gd` | Actual skeleton modifier samples, finite bounded quaternions and return to baseline; visual acceptance remains separate |
| Army logic | `lane_army_cases.gd` | Paired waves, all lanes engaged, caps, once-only rewards, reset and core outcomes |
| Independent combined stress | `traversal_army_stress.gd` | Projectile/pulse/army/audio coupling, focus/pause/reset, caps and 20 simulated minutes without invalid state |
| Controls/settings | `input_binding_cases.gd` | Persistence, collisions/reserved keys, keyboard navigation, small viewport, malformed and oversized input rejected |
| Audio | `build-traversal-audio.py --check`, `traversal_audio_cases.gd` | Eight exact PCM files, bounded cue flood, mute/pause/focus/disposal, finite mix headroom |
| Existing behavior | `native_acceptance.gd`, film and world flow suites | Training, cinematic playback and repeated scene transitions still work |
| Package integrity | `traversal_security_cases.py`, `package-native.py` | Reject unsafe paths/counts/flags/offsets/checksums/secrets; all runtime files, assets and notices present |
| Publication | `release_traversal_cases.py`, `release-native.py` | Failed/missing evidence and substituted assets block publication; exact remote tag and downloaded bytes checked |
| Render and interaction | Actual Forward+ capture and native window review | Readable routes/roles/HUD, plausible motion, usable controls and visible response to input |

AI uses bounded fixed-step logic; 20 simulated minutes are not a 20-minute hardware performance measurement. Check live units ≤72, corpses ≤24 and pending attacks ≤96 at every step, including reset and capacity pressure. Report memory/object counts separately from frame time. Inspect logs for runtime errors even when the process exits zero.

## Visual and source standards

`art/concepts/long-lanes-army-concept.png` is generated concept art. It sets materials, silhouettes and atmosphere; it is not captured gameplay or evidence that the current procedural models match that fidelity. The existing Rama model retains its separate provenance. New army meshes, landmarks, movement, poses and sound are original project work.

Retain a source-hash manifest and exact renderer/adapter/resolution for every accepted capture. Never rename a preview into a full render or reuse stale test summaries. The software Vulkan renderer supports inspection but cannot establish gaming-GPU FPS. Audio numerical checks cannot establish perceptual music quality.

## Current evidence

Fresh recovered reports are being collected in `tests/evidence/`. Final accepted reports, source freeze, rendered review and release verification will be recorded here before publication. Unrun gates remain pending.

No proprietary Deadlock/Overwatch binaries, rigs, animation clips or textures were analyzed or copied by this milestone. It does not complete the full roster, online native authority, production art, accessibility playtesting or commercial visual-quality roadmap.
