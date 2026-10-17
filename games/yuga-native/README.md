# YUGA native production track

The production target is now a downloadable PC game. Browser compatibility is
optional. This branch establishes the native engine, original 3D environment,
asset import and analysis toolchain. **It is a single-player training foundation,
not the complete multiplayer game or a completed reconstruction of Deadlock or
Overwatch.** The existing browser game remains on `game/yuga-confluence`.

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

The [production roadmap](docs/NATIVE_PRODUCTION_ROADMAP.md) keeps full-game
requirements open. The next game work is a native protocol-2 client using the
existing authoritative arena server, rather than discarding the tested browser
simulation. Production hero sculpting/retopology, richer animation, gameplay
content, multiplayer operations and hardware profiling require their own gates.
