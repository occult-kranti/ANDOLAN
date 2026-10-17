# Longer lanes, traversal and army verification

The base traversal/army evidence below is historical to `yuga-traversal-armies-2026-10-17`. The current **siege extension** is tracked in [SIEGE_MILESTONE.md](SIEGE_MILESTONE.md): cannon carts, royal chariots, committed blast warnings, four original cues, and immediate Siege practice. Fresh full-setup evidence is in [siege-setup/summary.json](evidence/siege-setup/summary.json); independent combat/pose review is in [siege-qa/REVIEW.md](evidence/siege-qa/REVIEW.md). The new [public siege review](evidence/siege-published/REVIEW.md) records 62 verified assets and a bounded actual downloaded-Linux run at source `35b20429d2b34f06f2907d5739cf4877aac597ab`. The original release counts below are historical.

Release status: published at `yuga-traversal-armies-2026-10-17` from `395986a512ecabe874710048a19bd0fdd0a71f89`. Local and CI gates, full capture, public release bytes and actual published Linux window checks passed. Only a completed report tied to current source establishes a passing gate. Earlier pre-outage results in `TRAVERSAL_ARMY_RECOVERY_2026-10-17.md` are historical, not the acceptance evidence for recovered source.

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

AI uses bounded fixed-step logic; 20 simulated minutes are not a 20-minute hardware performance measurement. Check live units ≤72, corpses ≤24, total unit nodes ≤96 and pending attacks ≤72 at every step, including reset and capacity pressure. Report memory/object counts separately from frame time. Inspect logs for runtime errors even when the process exits zero.

## Visual and source standards

`art/concepts/long-lanes-army-concept.png` is generated concept art. It sets materials, silhouettes and atmosphere; it is not captured gameplay or evidence that the current procedural models match that fidelity. The existing Rama model retains its separate provenance. New army meshes, landmarks, movement, poses and sound are original project work.

Retain a source-hash manifest and exact renderer/adapter/resolution for every accepted capture. Never rename a preview into a full render or reuse stale test summaries. The software Vulkan renderer supports inspection but cannot establish gaming-GPU FPS. Audio numerical checks cannot establish perceptual music quality.

## Current evidence

The complete cloud setup passed, including 225 TypeScript tests and 20 native/specification/security report files; its exact command, log and reports are archived under `docs/evidence/traversal-armies-setup/`. Rendered review then prompted a bounded UI/material/unit-art pass and explicit recovery from malformed saved settings. Fresh affected-suite reports supersede the earlier source hashes:

| Final focused check | Result | Evidence under `tests/evidence/` |
| --- | --- | --- |
| Physical traversal / rig poses | 36 / 24 passed | `traversal-cases-recovered.json`, `traversal-pose-recovered.json` |
| Army owner simulation | 21 passed; 24,000 ticks = 20 simulated minutes | `lane-army-cases.json` |
| Independent combined scene | 36 passed; 1,187 physics frames plus a separate 24,000 army ticks | `traversal-army-stress-final.json` |
| Package malformed-input checks | 27 passed | `traversal-security-final.json` |
| Controls and settings recovery | 39 passed | `input-bindings-recovered.json` |
| Audio | 39 passed in normal and accelerated clocks | `traversal-audio-runtime.json`, `traversal-audio-runtime-fixed60.json` |
| Extended world / lighting | 27 / 30 passed | `traversal-world/physics-ui-material-r3.json`, `traversal-world/lighting-material-r3.json` |
| Map specification / navigation | 12 / 30 passed | `world-plan-traversal-recovered.json`, `world-map-traversal-recovered.json` |

The independent soak recorded maxima of 64 live units, 64 unit nodes, eight corpses and 20 queued attacks. A separate capacity-pressure fixture reaches the exact 72-live limit and confirms paired spawn overflow is deferred. Both spawn-to-ring approaches measured about 33.065 m and stayed within the 18 m/s tether cap. Real projectiles triggered damage and audio; kill rewards across all three roles were awarded once. Reset/focus/overview and simultaneous core outcomes were exercised.

The first real preview is preserved under `docs/evidence/traversal-armies-render-r1/`: its HUD and art shortcomings are documented rather than replaced by the generated concept. Final capture is archived in `docs/evidence/traversal-armies-render-r2/`: 180 rendered frames, 360 physics ticks, six seconds at 1280 × 720 and five supplementary stills. All 214 captured sources match the real local export inventory. Maximum recorded speed was 18 m/s; every sampled player/rig state was finite. The capture uses software Vulkan and does not establish hardware FPS. The release validator passes 125 adversarial checks, including mismatched source, substituted media and omitted failed reports.

Portable Linux OS-input review is archived separately in `docs/evidence/traversal-armies-window-r2/`. It exercises title-to-world, remap/persistence/reset, movement, flight, pause, day/night, overview, round reset and return to the courtyard using XTest input to the actual packaged window. Public CI rebuild passed. All 46 public assets were independently downloaded and verified; the exact published Linux build passed a bounded OS-input repeat. See `docs/evidence/traversal-armies-published/REVIEW.md`. Windows has archive validation but no execution review.

No proprietary Deadlock/Overwatch binaries, rigs, animation clips or textures were analyzed or copied by this milestone. It does not complete the full roster, online native authority, production art, accessibility playtesting or commercial visual-quality roadmap.
