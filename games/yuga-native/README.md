# YUGA native production track

**Start a new task:** [repository handoff](../../docs/START_HERE.md) → [build handbook](docs/BUILD_HANDBOOK.md). The handbook maps features to files and provides setup, tests, art, capture, packaging and agent handoff instructions. Use the [research brief](docs/research/RESEARCH_BRIEF.md) for Reddit findings, mythology, selected reading and reuse decisions; use the [workspace guide](../../docs/WORKSPACE_AND_CLEANUP.md) for cloud cleanup and recovery.

The [full-game production roadmap](docs/FULL_GAME_PRODUCTION_ROADMAP.md) is the
execution guide from this preview to the intended competitive game. Its
[design master](docs/GAME_DESIGN_MASTER.md) specifies the player journey, roster,
combat, world and economy; the [dependency backlog](docs/ROADMAP_BACKLOG.json)
records owned tasks and acceptance evidence. The proposed production target is
6v6 with 18-minute matches; the current browser authority is 3v3/480 seconds.
The [research and engineering desk](docs/RESEARCH_ENGINEERING_DESK.md) handles
bounded requests from those workstreams. Its [BRUTAL assessment](docs/research/BRUTAL_STACK_DECISION.md)
retains Godot and Blender for production and records what a future engine change
would need to demonstrate.

The production target is now a downloadable PC game. Browser compatibility is
optional. This branch establishes the native engine, original 3D environment,
asset import and analysis toolchain. **The current native build contains local
training, a combat film and offline three-lane army practice with flight, grappling and siege vehicles. Online native matches and the
full production visual target remain open.** The existing browser game remains
on `game/yuga-confluence`.

[Download the siege and lane-army preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-siege)
for Linux or Windows, tagged at `35b20429d2b34f06f2907d5739cf4877aac597ab`.
All 62 public release assets pass independent checksum verification. The exact
downloaded Linux package passed actual title/world entry, keyboard siege entry,
F5 ordinary reset and title return. This bounded repeat is separate from the
broader local review. Windows is archive/resource-validated and unexecuted.
See the [milestone verification](docs/SIEGE_MILESTONE.md),
[actual rendered review](docs/evidence/siege-render-r2/SIEGE-RENDER-REVIEW.md),
[local Linux window review](docs/evidence/siege-window-r2/REVIEW.md) and
[public package verification](docs/evidence/siege-published/REVIEW.md).
Earlier traversal, cinematic, map and courtyard archives remain historical releases.

The current [siege milestone](docs/SIEGE_MILESTONE.md) adds cannon carts, royal chariots and immediate Siege practice. It also records the five parallel tasks and a staffing-dependent estimate for reaching the concept-art target; completion and release evidence are tracked there.

The [Triad relay milestone](docs/TRIAD_MILESTONE.md) now adds capture/contest/supply, three original stations, a relay HUD and clearer siege warnings on this branch. Try **Escape → Visit Lotus relay** in Confluence. The milestone records the exact acceptance/publication status and the [TF2 source study](docs/research/TF2_REUSE_STUDY.md); no TF2 code or assets were imported.

## Run the source

Install Godot **4.6.3 standard**, then open `project.godot`, or run from the
repository root:

```sh
godot --editor --path games/yuga-native
godot --path games/yuga-native
```

The production rendering path uses **Forward+**: PBR materials, directional
shadows, ambient occlusion, glow, animated water and warm lantern lighting.
For a computer without a working Vulkan driver, the explicit fallback is:

```sh
godot --path games/yuga-native --rendering-method gl_compatibility
```

The compatibility path has fewer rendering features. The cloud worker has no
physical GPU; software-rendered evidence cannot establish consumer GPU frame
rates, latency or visual parity with a commercial game.

## Current playable content

Choose **EXPLORE CONFLUENCE** from the title for a 140 × 260 m city with
coastal ghats, temple avenue, metro gardens and reed courts. Three longer routes
contain eight landable stone decks and ten glowing tether anchors. Finite-energy
flight and grappling use capsule collision and bounded speeds. Day/night lighting,
animated coast/swamp water, an overview and travel shortcuts remain available.

Paired 30-second waves of spear soldiers, bow guards and banner commanders fight,
threaten local cores and grant once-only player last-hit gold. Mirrored cannon
carts can reinforce each lane every third wave;
royal chariots can reinforce the centre every fifth. Both sides must have spawn
clearance and capacity for a reinforcement pair to appear.

Press **Escape → Siege practice** to enter an immediate six-unit central drill.
Destroy an enemy engine before its marked attack lands to cancel the shot.
**Restart lane practice**, or F5 during play, restores the ordinary round and
arrival spawn. Siege blasts damage troops; hero health and death are not
implemented in this practice mode.

This is offline practice: the browser's 140 × 170 m baseline and production army,
economy and network rules remain separate. Native online matches, jungle combat
and the full competitive rules are still open roadmap work.

In the courtyard:

One original Lanka-inspired coastal courtyard, a revised skinned Rama model,
nine animation clips, third-person movement and camera collision, a solar bow,
sunburst, dash, five resetting targets, procedural sound cues, pause, saved
settings, restart and return to title. The environment contains carved arches,
colonnades, lotus details, stone/brass/indigo PBR surfaces, water channels,
lanterns, marsh plants and a distant skyline. Its actual meshes and materials
are described in [the art record](art/README.md).

| Action | Control |
| --- | --- |
| Move / aim / fire | WASD / mouse / left click |
| Sprint / jump | Shift / Space |
| Sunburst / dash | Q / E |
| Reload | R |
| Confluence flight / tether | F / G |
| Rise / descend while flying | Space / Ctrl |
| Help and persistent keyboard remapping | F2 |
| Pause and release cursor | Escape |
| Reset courtyard | F5 |
| Confluence day / night | N |
| Confluence atlas view | F1 |
| Reset Confluence practice round | F5 |

The native training controls and ability rules are explicit experiments. They
are not a port of all fourteen browser hero kits. Assets retain their provenance
in [NOTICE](NOTICE/ASSET-NOTICE.md). The current Rama revision adds original
cobalt/ivory costume, hair, bow-grip details and PBR textures while retaining
the existing anatomy, 164-bone rig and nine animation curves. It is an incremental
art pass; a finished sculpt, fitted cloth and richer action animation remain open.

## Confluence duel animation milestone

Choose **WATCH CONFLUENCE DUEL** from the source build's title screen for the
24-second Rama–Ravana sentinel study: a guarded shot, a warned wave, an evade
and a countershot. Two skinned actors use nine clips each, with a shared timeline
for cameras, effects, captions and original synthesized audio. The viewer has
play/pause, replay, a scrubber, captions, reduced flashes, a static-camera option
and return to the courtyard. Space toggles playback; arrow keys seek; Escape returns.

The [screenplay](docs/COMBAT_FILM_SCRIPT.md),
[runtime timeline](assets/cinematics/confluence-duel.json) and
[direction review](docs/COMBAT_FILM_REVIEW.md) record the four review rounds.
Revision 4 passes 20 screenplay/resource, 42 native animation/viewer and five
motion-continuity checks. Those checks include a repaired guard-reset transition;
all action, effect and audio times remain unchanged.

[Watch the complete 24-second film](https://raw.githubusercontent.com/occult-kranti/ANDOLAN/game/yuga-native-production/games/yuga-native/docs/evidence/combat-film-r4/yuga-confluence-duel.mp4)
at 1280 × 720 and 24 fps, with original stereo audio. Independent checks confirm
all 576 rendered frames and zero measured audio offset against the source mix.
The [local Linux package review](docs/evidence/combat-film-package/REVIEW.md)
passes after extraction and actual keyboard/mouse testing of playback, seeking,
replay, accessibility toggles, saved mute, returns and courtyard movement.
Windows archives and resources validate; Windows execution remains untested.

The [r2 cinematic preview release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-confluence-duel-2026-10-17-r2)
is published. Its [build and release workflow](https://github.com/occult-kranti/ANDOLAN/actions/runs/39002862685)
succeeded for tag `yuga-confluence-duel-2026-10-17-r2`. All 26 uploaded release
assets were independently downloaded and their manifests/checksums verified. The
[published Linux ZIP](docs/evidence/combat-film-published-r2/published-linux-window-review.json)
was extracted and run: title entry, pause, seeking, pre/post-hit health, replay,
Escape return and saved mute pass. This is a bounded repeat; it does not claim
that every earlier local flow was rerun. Windows remains unexecuted. See the
[published release review](docs/evidence/combat-film-published-r2/REVIEW.md) for
exact hashes and the explained import differences from the local pack. Existing
map-preview downloads are unchanged.

This is a scripted animation prototype. Visual health receipts are separate from
multiplayer authority; the commercial visual target, native multiplayer and full
hero roster remain open. Audio correspondence is checked numerically; listening
quality and consumer-GPU performance are not established here.

## Native analysis

REA 6.5.0 has now been exercised through Ghidra 12.1.4 on an original compiled C
fixture. ELF layout inspection, decompilation and function relationships pass.
The [reproduction instructions](tools/native-analysis/README.md) and
[exact evidence](docs/evidence/native-analysis-toolchain.json) identify the
inputs and what was recovered. These are real binary-analysis results, but
their target is the authored fixture.

The [Deadlock intake](../yuga/docs/research/DEADLOCK_NATIVE_INTAKE.md) and
[Overwatch intake](../yuga/docs/research/OVERWATCH_NATIVE_INTAKE.md) record the
actual game-input gap and tool requirements. Their early provider-readiness
failures predate the successful provisioning above. No commercial game client,
replay or assets have been analyzed. A complete installed client would still
not supply server-only implementation or recover exact original source from
optimized machine code.

## Verification and next production stages

[Native tests](tests/README.md) exercise physics, collision, projectiles,
reload/reset/pause and sampled animation transforms. Scripted headless tests
are separate from actual native-window screenshots and input checks. Build and
public download status are recorded only after those checks complete.

The [art review](art/production/ART_DIRECTION.md) records actual rendered defects
and visual gates. [Hero review instructions](docs/HERO_RENDER_REVIEW.md) reproduce
the staged front/rear/side and animation-pose captures. These still frames do not
prove smooth continuous animation. Concept images remain separate from runtime
screenshots and exported 3D assets.

The [reusable-systems study](docs/research/REUSABLE_GAME_SYSTEMS.md) identifies
versioned Godot examples, Dota 2 tools and REA forks with separate code/asset
licenses. [Physics and graphics notes](docs/research/PHYSICS_GRAPHICS_STUDY.md)
connect inspected sources to an implemented projectile lifetime correction.
The [character reuse audit](docs/research/CHARACTER_REUSE_AUDIT.md) compares
reconstructed engines and reusable game assets; the
[reference import](docs/research/REFERENCE_CHARACTER_IMPORT.md) records the
licensed TPS character's real Godot import, clip-name repair and unapplied bone
mapping. It is a separate study asset, with no automatic replacement of Rama.

The [task board](docs/PRODUCTION_TASK_BOARD.md) defines four rounds per subgoal:
inspect, build, verify, then report/integrate, with separate file ownership.

The earlier [native milestone roadmap](docs/NATIVE_PRODUCTION_ROADMAP.md)
records the foundation sequence. Use the full-game roadmap above for current
priorities: native protocol-2 integration, a shared 3D collision/elevation
contract, production hero and motion quality, then a complete native match.
Production sculpting/retopology, gameplay content, operated services and physical
hardware profiling require their own gates. The roadmap checker verifies the
ledger structure; it does not certify that the game or its art is finished:

```sh
python3 games/yuga-native/tools/check-roadmap.py
```
