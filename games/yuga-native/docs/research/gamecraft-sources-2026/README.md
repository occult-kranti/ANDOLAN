# Game craft sources for the YUGA panel

This packet records selected chapters and two real glTF sample assets used during the physics, combat, motion and world review. The chapter notes below summarize specific sections read on 25 November 2026. They are questions and design constraints for the team, rather than evidence that a combat change is balanced or an export works in a match. [Fetched-page records and video metadata](source-audit.json) · [Executed sample results](sample-results.json)

## Books and technical references

| Source and section | What was inspected | Application to YUGA |
| --- | --- | --- |
| Hunicke, LeBlanc and Zubek, “MDA: A Formal Approach to Game Design and Game Research” | Read the five-page 2004 paper, including the distinction between rules, player interactions and intended experiences, plus its tuning examples. | For each proposed skill, record the intended player experience, the runtime rule and the interaction observed in a playtest. Test whether allies can coordinate and opponents can read the counter before attributing a feeling to the design. [Original paper](https://users.cs.northwestern.edu/~hunicke/MDA.pdf) |
| Robert Nystrom, *Game Programming Patterns*, “Game Loop” | Fixed and variable update steps, and interpolating an apparent position between updates. | Keep authoritative releases, damage and movement on the 20 Hz game clock. Test render interpolation separately, especially after a correction or interrupted move. [Chapter](https://gameprogrammingpatterns.com/game-loop.html) |
| Robert Nystrom, *Game Programming Patterns*, “State” | The finite-state example and entry actions that initialize the new state's presentation. | Specify entry, active, interrupt and exit ownership for each vault or cast. The physics review uses those boundaries to examine a knockout during a vault and the subsequent respawn. [Chapter](https://gameprogrammingpatterns.com/state.html) |
| Glenn Fiedler, “Fix Your Timestep!” | Fixed-step accumulation, a simulation backlog that grows faster than it can be processed, and interpolation between previous and current state. | Bound catch-up work in the component that owns the clock, then measure long-frame recovery. Recorded replays need the same inputs and rules; cross-platform determinism remains a separate test. [Article](https://gafferongames.com/post/fix_your_timestep/) |
| Daniel Shiffman, *The Nature of Code*, “Forces” and “Particle Systems” | Force accumulation, mass, and particles that own motion and finite lifetimes. | Give non-authoritative embers, dust and motes an explicit birth, age and end. Keep the ground warning and damage event independently readable when individual cosmetic particles expire. [Forces](https://natureofcode.com/forces/) · [Particle systems](https://natureofcode.com/particles/) |
| Robert Nystrom, *Game Programming Patterns*, “Object Pool” | Fixed-capacity pools and options when a pool is full, including choosing a less important active sound to replace. | Define and test a bounded overflow policy for effects and audio. Reserve legibility for attack warnings and impact cues before spending the budget on decorative fragments. [Chapter](https://gameprogrammingpatterns.com/object-pool.html) |
| Pharr, Jakob and Humphreys, *Physically Based Rendering*, 4th ed., §9.6 | The rough-surface introduction and microfacet distribution, masking and reflection discussion. | Compare bronze, cloth and stone under the same lighting. A change to base color alone does not establish a changed roughness response. Record the material and light setup along with close views. [Chapter](https://pbr-book.org/4ed/Reflection_Models/Roughness_Using_Microfacet_Theory) |

The team already maintains a larger source catalog and a separate record of what each historical research round actually used. [Game resource library](../../../../../research/game-resource-library/README.md) · [Research brief](../RESEARCH_BRIEF.md)

## Two runnable animation samples

The two GLBs below are unchanged inputs from Khronos Group's sample repository at revision `e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea`. The local binaries were compared byte for byte with that upstream revision. Each source folder retains its own metadata and license notice.

| Sample | What was run in Blender 4.3.2 | Credits and terms |
| --- | --- | --- |
| [Fox](samples/fox/Fox.glb) | Imported one 24-joint skeleton. Sampled 13 poses each in Survey, Walk and Run, and measured changing foot and tail offsets relative to the hip. The result is a clip-import and joint-sampling check. | PixelMannen's model is CC0. tomkranis' rigging/animation and the AsoboStudio/scurest glTF conversion are CC BY 4.0. [Upstream asset](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/Fox) · [Metadata](samples/fox/metadata.json) · [License](samples/fox/LICENSE.md) |
| [Animated Morph Cube](samples/animated-morph-cube/AnimatedMorphCube.glb) | Imported one mesh with `Basis`, `thin` and `angle` shape keys. Across 13 samples the two animated weights ranged from 0 to approximately 0.966 and 0.957. | Microsoft’s 2017 model is CC0. Repository metadata and the license file carry their stated attribution terms. [Upstream asset](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/AnimatedMorphCube) · [Metadata](samples/animated-morph-cube/metadata.json) · [License](samples/animated-morph-cube/LICENSE.md) |

The Fox asset is a quadruped. The probe reports the original imported coordinate units, and samples alone do not establish planted feet, correct humanoid retargeting or gameplay integration. The morph sample establishes that Blender can read animated glTF weights. A YUGA facial action still needs a test on the actual character and the target runtime.

Run the independent import and pose probe from the repository root:

```sh
blender -b -t 1 --factory-startup --python-exit-code 1 \
  -P games/yuga-native/docs/research/gamecraft-sources-2026/probe_samples.py
```

The script verifies both binary hashes, loads each in a fresh empty Blender scene and writes [sample-results.json](sample-results.json). The actual run used Blender 4.3.2 and completed successfully. The Fox clip displacements are relative to its hip, which distinguishes articulated motion from moving the entire actor.

## Video review queue

These are verified public video titles and uploader identities. YouTube returned HTTP 403 for direct access in this environment, and a public English-caption endpoint returned an empty payload for the first two. Video frames and transcripts were not reviewed. The links below are for a later source review with access to playback.

| Video | Relevance to investigate |
| --- | --- |
| Jan Willem Nijman, “The art of screenshake,” Dutch Game Garden, published 16 December 2013 | Compare impact, movement and camera effects with reduced-motion and readability settings. [Video](https://www.youtube.com/watch?v=AJdEqssNZ-U) |
| Martin Jonasson and Petri Purho, “Juice it or lose it,” uploaded by grapefrukt, published 24 May 2012 | Review how animation, tweening and particles affect presentation; assess each layer under multiplayer load and with effects reduced. [Video](https://www.youtube.com/watch?v=Fy0aCDmgnxg) |
| “Animation Bootcamp: An Indie Approach to Procedural Animation,” GDC Festival of Gaming | Review procedural-pose methods and compare against the existing authored Hanuman actions. [Video](https://www.youtube.com/watch?v=LNidsMesxSE) |
| “Math for Game Programmers: Building a Better Jump,” GDC Festival of Gaming | Review jump-design mathematics against the actual authoritative vault. [Video](https://www.youtube.com/watch?v=hG9SzQxaCm8) |

## Work performed across the five passes

1. Located the existing resource database, hero handoff and prior animation/source audits.
2. Read the named sections of the public books and article, recorded access hashes and sent focused checks to each domain owner.
3. Fetched and compared the two licensed sample assets with their pinned upstream bytes, then imported and sampled them in Blender.
4. Challenged the findings against YUGA's actual authority, the Fox's nonhuman skeleton, source licenses and the limits of the unavailable videos.
5. Preserved the source notices, test script, measured results and the next review targets in this packet.
