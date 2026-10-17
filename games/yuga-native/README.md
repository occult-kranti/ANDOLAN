# YUGA native production track

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
training and a traversable three-lane map preview. Online native matches and the
full production visual target remain open.** The existing browser game remains
on `game/yuga-confluence`.

[Download the native art development preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-art-2026-10-17)
for Linux or Windows, with rendered review evidence. The extracted Linux package
was exercised in this cloud worker; Windows is archive-validated but unexecuted.
See the [production review](docs/PRODUCTION_REVIEW.md) for exact scope and hashes.

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

Choose **EXPLORE CONFLUENCE** from the title to walk a 140 × 170 m city with
coastal ghats, temple avenue, metro gardens and reed courts. The scene combines
eight original architecture presets and seven nature presets across 63 deliberate
placements, animated coast/swamp water, day/night lighting, an atlas and travel
shortcuts. It uses the current authority's static map coordinates; objective and
camp markers are visual previews. Live armies, objective collision/state and
networked matches are still separate integrations. See the
[world production plan](docs/WORLD_PRODUCTION_PLAN.md) and
[actual map review](docs/CONFLUENCE_MAP_REVIEW.md).

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
| Pause and release cursor | Escape |
| Reset courtyard | F5 |
| Confluence day / night | N |
| Confluence atlas view | F1 |
| Return to Confluence arrival point | F5 |

The native training controls and ability rules are explicit experiments. They
are not a port of all fourteen browser hero kits. Assets retain their provenance
in [NOTICE](NOTICE/ASSET-NOTICE.md). The current Rama revision adds original
cobalt/ivory costume, hair, bow-grip details and PBR textures while retaining
the existing anatomy, 164-bone rig and nine animation curves. It is an incremental
art pass; a finished sculpt, fitted cloth and richer action animation remain open.

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
