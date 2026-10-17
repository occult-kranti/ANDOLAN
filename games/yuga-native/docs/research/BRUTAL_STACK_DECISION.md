# BRUTAL and the YUGA production stack

Reviewed 17 October 2026. **Keep Godot 4.6.3 Forward+, Blender and portable glTF
assets for the current production milestone.** BRUTAL is a useful low-level C#
framework to study, but replacing the current engine with it would require us to
build a renderer, editor, scene system and animation runtime before improving the
game. Reconsider an engine or subsystem only against a measured requirement.

This is a bounded source and package review, plus an actual Godot IK experiment.
It is not a BRUTAL benchmark, a commercial-game reconstruction or proof of
Deadlock/Overwatch visual quality.

## What the primary BRUTAL material establishes

The repository was inspected at
[`ahwootech/BRUTAL@a25cdf80b2a15530e7da6cff744def9d841ad3c3`](https://github.com/ahwootech/BRUTAL/tree/a25cdf80b2a15530e7da6cff744def9d841ad3c3).
Its complete README and license were read; selected implementation scopes are
listed below. GitHub metadata reported repository creation on 14 October 2026,
5,585 C# files in the returned tree, zero `.csproj`, `.sln`, `.slnx`, `.props` or
`.targets` files, and no published GitHub releases at retrieval. That describes
the public repository snapshot, not the age of the underlying studio technology.

| Question | Verified source finding | YUGA consequence |
| --- | --- | --- |
| Is it a complete engine? | README explicitly says there is **no editor, no scene graph and no renderer**, and that these are outside its intended scope. | It does not supply the missing hero/art/game production pipeline. |
| What does it provide? | C# native interop, memory/math/collections, job scheduling, Vulkan/OpenGL/window/input bindings, mesh/texture/glTF utilities, and bindings for Jolt, Box2D, RakNet and audio libraries. | Useful components and implementation references; each still needs integration and its own acceptance test. |
| Does it provide finished shooter animation? | glTF loader/schema code handles asset data. The inspected tree includes Jolt skeleton bindings, but no demonstrated animation graph, retargeting tool, authored hero set or shooter framework was found in this bounded review. | Importing a skeleton or binding Jolt does not solve bow carry, grip, foot contact, action transitions or content authoring. |
| Can it be built from this checkout? | README says project/solution/build files are coming and directs consumers to NuGet meanwhile; the returned tree contains none of those definitions. | No reproducible source build was established. Do not describe cloning it as a complete build. |
| What are the advertised prerequisites? | README names .NET 10, Windows or Linux, and Vulkan 1.3-capable graphics hardware when rendering. Its first sample opens a GLFW window with no graphics API. | The sample is not a rendered scene. No .NET executable was present on PATH in this worker; no SDK was installed for an unrelated rewrite. |
| Are packages real? | NuGet Core `2026.10.1`, Gltf `2026.10.2`, Glfw `2026.10.4` and Vulkan.Abstractions `2026.10.2` were listed. Core and Gltf archives were downloaded and inspected. Their assemblies target `net10.0`. | Package metadata, SHA-256, ZIP CRC and notice presence were verified; C# compilation/native execution was not. |

### The RimWorld claim

BRUTAL's maintainers state that Ludeon built its **Waylith** engine on BRUTAL to
move RimWorld off Unity. Their README also attributes a two-to-four-times
performance report to Ludeon's own tests and links a
[Steam announcement](https://steamcommunity.com/games/294100/announcements/detail/672882362547178634).
The Steam announcement was not read here: that host is outside this worker's
configured allowed network hosts. The observed evidence is the framework
maintainers' primary repository statement; there was no independent RimWorld
build or benchmark. A RimWorld-specific result would not predict this 3D
multiplayer game's frame time or art quality.

### Licensing is more specific than “free C#”

[`LICENSE.txt`](https://github.com/ahwootech/BRUTAL/blob/a25cdf80b2a15530e7da6cff744def9d841ad3c3/LICENSE.txt)
is **BRUTAL License v1.0**, an MIT-based custom license, not unmodified MIT.
For distributed products using it, it requires the copyright in credits,
an appropriately visible BRUTAL logo before gameplay/primary function, and
shipping `NOTICE.txt`. The license text exempts products unable to display
graphics from the logo clause and permits written waivers; do not infer an
automatic nonprofit exemption from the README's offer to waive it. The README
says the license was not yet submitted for OSI approval.

Third-party components retain their own terms. The inspected FMOD notice says
commercial use may need a separate Firelight license; the Jolt notice is MIT.
RakNet's notice records native binaries and component-specific terms. No BRUTAL
code or binary is added to the shipped YUGA game by this review, and its branding
requirement is not silently added to the launch flow.

## Useful code lessons, with reading scope

| Pinned file | Scope actually read | Transferable lesson |
| --- | --- | --- |
| `Brutal.Gltf/GltfApi/GltfLoader.cs` | Lines 1–180: loader interfaces, cached buffers/images, buffer-view range handling. | Treat imported asset access as checked, attributable data; an import operation is not an animation-quality result. |
| `Brutal.Gltf/GltfApi/GltfLoader.Transform.cs` | Lines 1–220: coordinate/scale conversion contract and opening implementation. | Coordinate conversion must consistently transform nodes, geometry, normals/tangents, winding, inverse binds and animation tracks. Converting only the visible mesh breaks skinning. This is a conceptual lesson; no code was ported. |
| `Brutal.Concurrency/Jobs/JobScheduler.cs` | Lines 1–200: explicit runner count, weighted queueing, execution/wait/abort, metrics access. | Bound worker concurrency, distinguish synchronous waits from productive parallel work, and collect consistent metrics. A native job scheduler is not an autonomous agent service. |
| README first-window sample | Entire sample; not executed. | Verify the rendered result of an experiment, not merely a created window. |

Generated animation-schema and SkeletonMapper binding files were retrieved for
identification but are not claimed as a complete animation-system review.
No Reddit threads or additional game-design books were read in this pass.

## Stack decision and the condition that could change it

| Component | Decision now | Required evidence before expanding/replacing it |
| --- | --- | --- |
| Godot 4.6.3 Forward+ | **Use.** Existing native project, real imports/physics/captures and portable builds work. | A representative populated arena on a declared physical GPU; software-rendered cloud captures establish appearance, not shipping performance. |
| Blender 4.3.2 + glTF | **Use.** Preserve original source, rest-pose contracts, licenses and portable artifacts. | One hero with convincing authored bow actions, locomotion and contact, then repeat the production process on a second different hero. Tool installation is already complete; content quality is the remaining work. |
| Godot skeleton modifiers | **Use a bounded original implementation.** Actual installed TwoBoneIK3D passes five synthetic solver cases; see the [desk ticket](../RESEARCH_ENGINEERING_DESK.md). | Actual Rama grip/orientation, split-bone deformation, action cancellation and rendered continuous-motion review. |
| Godot physics / built-in Jolt option | **Evaluate within the existing engine first.** Do not add the external Jolt extension, which is in maintenance mode, automatically. | Record the chosen backend and run the same stairs, floor seams, ledges, fast-projectile and collision-capacity fixtures. Do not claim cross-platform deterministic physics. |
| Existing TypeScript authoritative server | **Retain while testing the elevation contract.** It supplies current room, identity, economy and match rules. | Shared 3D collision, elevated aim/zone semantics, native prediction/reconciliation and two-client stairs/bridge proof. Existing x/z collision is insufficient for a traversable multi-level city. |
| Khronos glTF-Validator | **Adopt as an independent asset-format gate.** Apache-2.0 upstream at `602c54043ba66856b2e68c40fdf2bced975cdb8a`; independent reviewer read its README, license, Node API and relevant issue catalogue. | Pin package/integrity and validate actual exported bytes; fail on `issues.numErrors > 0`, preserve warnings. This cannot accept topology, animation intent or visual quality. |
| BRUTAL | **Study / defer runtime adoption.** Useful for a specifically justified C# native subsystem or custom-engine project. | A bounded prototype must beat the existing path on the same named requirement while accounting for renderer/editor/content-tooling work and distribution terms. |
| Unreal Engine 5 | **Conditional comparison candidate.** A mature alternative for a future matched production experiment, not a tool already validated here. | Obtain appropriate Epic access/terms and a suitable development machine, then import identical owned assets and compare motion/workflow/frame time. No Unreal install, EULA review, build or benchmark was done in this pass; no current royalty threshold is asserted. |
| REA/Ghidra, replay parsers and reconstructed games | **Keep the research lane bounded.** Existing source/license audits already identify reusable references. | Each study needs an accessible input, bounded question, provenance and behavior test. A parser or binary-analysis tool does not confer commercial art rights or recover an entire production game automatically. |

The independent countercheck identified three genuine reasons to revisit this
choice: populated-scene rendering cost, repeatable animation production across
different rigs, and divergent native/server collision models. Proposed tests:

1. Six heroes, 36 lane units and representative effects in a repeatable 1080p
   sequence on a declared target GPU. A proposed target is p95 frame time at or
   below 16.7 ms. If two focused measured optimizations leave an engine-specific
   bottleneck, run an equivalent Unreal fixture before deciding migration.
2. Idle/run/strafe/aim/fire/cast/jump/landing on two distinct heroes, with grip,
   foot support, cancellation and silhouette review. Separate bad assets from
   an unsupported engine requirement before changing engines.
3. Six clients under controlled latency/jitter, with a proposed p95 server-step
   budget below 25 ms at the present 20 Hz authority. Require bounded correction,
   consistent cover/hit decisions and rejection of impossible movement. Persistent
   collision divergence triggers an authority experiment, not extra smoothing.

These are acceptance targets, not measurements achieved by the current build.
The worker exposes five logical CPUs but has a four-core cgroup CPU quota, no
`/dev/dri`, and roughly 6.5 GB free during review. Run one heavy software renderer
at a time; do not benchmark an Unreal/BRUTAL GPU claim on that environment.

## Reproduction and source fingerprints

The package audit inspects fixed archives without extracting or running vendor
code. It uses normal HTTPS/proxy handling:

```sh
python3 games/yuga-native/tools/research/audit-brutal-packages.py \
  --cache /tmp/yuga-brutal-research \
  --report games/yuga-native/docs/research/brutal-package-audit.json
```

The [saved audit](brutal-package-audit.json) records two successful archive checks,
their `net10.0` dependencies, notice hashes, and explicit `compiled: false` and
`rendered: false` fields. Total downloaded archive bytes: **195,819**.

| Retrieved source | SHA-256 |
| --- | --- |
| BRUTAL README | `291277fba0c596b4168eecf846feea4b88d8b29e2c1428ee608eee8121c5c3d7` |
| BRUTAL LICENSE.txt | `7cbc60f8090a323312294ea4e95fb0afbb2292b9d7017c0712b108d1cc914bd0` |
| BRUTAL NOTICE.txt | `9b71447f1484eb8a510da835e6a07c6fc4ec5e586f0af08791c9d8c51c7fcf3c` |
| GltfLoader.cs | `0ab37e28338dbf56875b26ac35a1e14e7bb9f12bd510deb47ba2830c09dd5381` |
| GltfLoader.Transform.cs | `22694f504a22b4139eebb2aa6d0d32729d33f284c6eac485cdf67c4c6773eef6` |
| JobScheduler.cs | `d8dd8f61745b3c743399d042b04a91dcba0f8c3dd1476189b4b4966cecb122de` |
| Core 2026.10.1 nupkg | `074ed2fde25c42548c283626c2b89d2028f349203dc2d2927d4ab0999a2386c4` |
| Gltf 2026.10.2 nupkg | `0bbf18f4988e7dbbd7fee02ea3b93965e6515f59277f977a1e7edafebb38d144` |

Package archives and downloaded source excerpts remain outside the product under
the temporary research directory. The decision and tests remain reviewable in
the repository; no background research service continues after this turn.
