# Art and material reuse: selected, tested decisions

Research cut: 17 October 2026, YUGA native source
`7c86cd430e2c878b4f5e6ba1b21f562b73fdc32f`. These are primary-source
recommendations, **not a Reddit ranking or community consensus**. The separate
[community report](community.md) records the fresh access failure. No Reddit
requests were made by this worker.

The highest-value work remains authoring the current character and troops.
The actual day face image
`evidence/visual-campaign/capture-shadow-confirm-world-day-r3/shadow-bias-depth2-face-day.png`
was opened: broad rope-like hair masses and abrupt temple/scalp coverage remain,
and the face still needs eyelid/lip/chin definition and lighting diagnosis.
`evidence/visual-campaign/art-review/film-samples/frame-00287.png` was also opened:
infantry retain blocklike torsos/limbs and the floor/skyline repeat strongly.
These are two inspected originals, not a new whole-film or motion review.
The current [handoff](../../VISUAL_CAMPAIGN_HANDOFF.md) and R2/R3 reviews remain
the broader evidence. Residual stippling is not proof that new skin textures
are needed; current lighting/material controls should be isolated first.

## Reuse decisions in production order

| Decision | Exact reusable element and source | Rights and integration limits |
| --- | --- | --- |
| **First: retain Blender and refine the owned source.** | Existing `art/production/reconstruction-rama.blend`, `art/hero-rama/` generator, and current hero GLB. Blender source reference `blender/blender@b3efe983cc585ef5283d84bc303367d1d6cd6771` (4.5.4): `source/blender/editors/sculpt_paint/sculpt.cc`, `curves_sculpt_add.cc`, and `source/blender/modifiers/intern/MOD_solidify.cc` expose sculpt, groom-stroke and garment-thickness mechanisms. | Blender code is GPL-2.0-or-later; fetched actual `doc/license/GPL-license.txt` plus source SPDX headers. This is authoring-tool use, not copying GPL implementation into Godot. Existing MakeHuman anatomy has its separate CC0 source record, and project hair/costume/bow have explicit CC0 dedication in `art/hero-rama/NOTICE.md`. The inspected 4.5.4 source is a reference, **not an upgrade** from the installed 4.3.2 pipeline or proof those versions behave identically. |
| **Retain the current rig; defer Rigify replacement.** | Prefer the release-matched **Blender 4.3.2 bundled Rigify**, `blender/blender@32f5fdce0a0a571a39198edf8d7b5d719bf59f2c/scripts/addons_core/rigify`, independently inspected in [ANIM-01](animation.md#exact-source-decisions). Its `utils/animation.py` FK/IK snap/bake and `rigs/limbs/limb_rigs.py` control/deform interfaces are authoring references. | GPL-2.0-or-later. A copied-scene authoring control rig could bake back to the original deform skeleton; replacing Rama's 164-joint rig would reopen skin, sockets and nine imported clips/23 runtime states. Tool GPL does not automatically license independent model geometry, while copied/generated Python UI code requires its own license check. No new rig was generated or accepted. |
| **Candidate for later fabric/stone bakes: Material Maker 1.6.** | `RodZill4/material-maker@b4fcad06f0b13785de423c42b36406df605c8321`: `addons/material_maker/nodes/weave.mmg` (grayscale width/rows/columns weave), `bricks_uneven.mmg` (uneven bond), `engine/nodes/gen_export.gd`, and `nodes/godot.tres.tmpl` under that add-on. | Root `LICENSE.md` is MIT and README says repository files use MIT unless otherwise specified; selected node files have no contrary notice. That grants reuse of these graphs/code, not rights to arbitrary imported community images. `project.godot` targets Godot 4.6, but the inspected export template is **Godot 3 `SpatialMaterial`, format 2**, so it is not a Godot 4.6.3 drop-in. Use an offline PNG bake with original `StandardMaterial3D` binding if advanced; no Material Maker execution or bake was done here. |
| **Reuse existing proven material bytes before new catalogs.** | Courtyard maps/geometry at `assets/environment/lanka_courtyard.glb` and `lanka_courtyard.metadata.json`; Microsoft SheenCloth `KhronosGroup/glTF-Sample-Assets@edc7c9e67c639d230715049ee31f9a96a6babbbe/Models/SheenCloth`. Actual asset license, metadata and original ORM were freshly fetched. | Generated courtyard geometry/textures are explicitly CC0; no root code license is inferred. SheenCloth images are CC0, but its LICENSE/metadata documents are CC-BY-4.0. Current selected ORM bytes match the retained local source. Neither source establishes authentic historical silk. No new Poly Haven/Kenney asset is cleared: no individual download/creator/license/hash was verified in this pass. |
| **Implemented, optional R9: exact static-mesh preflight.** | [Small CLI](../../../tools/reuse-art/README.md) calls `@gltf-transform/{core,extensions,functions}@4.3.0`, source commit `3b3afffbd4d3a29790c9fb166fa4c6755687154d`, especially `packages/functions/src/weld.ts`, `reorder.ts`, `hash-table.ts`, `compact-primitive.ts`; plus `meshoptimizer@0.24.0`, source `7b2d4f4c817aea55d74dcd65d9763ac2ca608026`, `js/meshopt_encoder.js`. | Both direct libraries are MIT; actual licenses and required notices are in the [tool notice](../../../tools/reuse-art/NOTICE.md). This reuses the meshoptimizer version already used by the LOD authoring path. Upstream meshoptimizer 1.0 was source-inspected, not installed/adopted. Dependency lock is local to the tool; no root package change or runtime library is added. |

Historical source check retained in the ledger: this art worker fetched
`blender/blender-addons@b42d68627734cb18af0e6f41537063984313a284` and examined
`rigify/__init__.py` (0.6.10, minimum Blender 4.0, GPL-2.0-or-later); generated
rig and limb source files were fetched but not fully read. That archived mirror
is superseded for adoption by the animation worker's release-matched source
above. This art worker read ANIM-01; it did not independently refetch those
Blender 4.3.2 files. No rig replacement is recommended.

Blender/Rigify are not prebuilt hero art. A useful bounded authoring packet is a
copy of the owned face/head source with eyelid, lip/chin and principal groom
forms revised while retaining the established rig interface. Require front,
three-quarter, side/orbit, day/night, aim and draw deformation evidence before
promotion. The rejected 800-triangle wisps are not a reusable accepted groom.
For troops, refine the existing shared silhouette and materials in
`scripts/lane_unit_art.gd` with five-role recognition and troop-cap resource
budgets intact. A generic low-poly pack would not by itself resolve the observed
blocklike quality or mythology/costume coherence.

A future Material Maker bake should output at most the current map count and
resolution for the selected material, with explicit channel/color-space
metadata. Current hero finish expects grayscale roughness in RED; courtyard
packed ORM expects roughness GREEN, metallic BLUE, AO RED. The inspected
Material Maker template agrees with that ORM packing, but its engine resource
format is obsolete. Test texture seams, mips and scale under matched lights;
normal changes also reopen the existing tangent/UV findings. Do not add a
procedural runtime shader just because an authoring graph exists. Neither
texture detail nor glTF optimization fixes repeated composition or face forms.

## The concrete adaptation and measured result

The new optional `tools/reuse-art/static-world-preflight.mjs` accepts a supported,
embedded, static GLB up to 64 MiB and writes only to a fresh external directory.
It welds **bitwise-identical** vertices and uses the meshoptimizer 0.24 index/
vertex reorder API with `target: 'performance'`. It does not simplify, quantize,
compress, regenerate normals/tangents or touch image pixels. Transparent BLEND
materials, skins, animations, morphs, unregistered extensions and metadata the
adapter cannot preserve are refused. This guard is especially relevant to the
hero's known UV/degenerate-corner findings and 164-joint animation interface.

Measured on `assets/environment/lanka_courtyard.glb`, SHA256
`1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33`:

| Property | Input | Scratch candidate |
| --- | ---: | ---: |
| Vertices, summed per primitive | 266,311 | 265,989 |
| Triangles | 135,654 | 135,654 |
| Primitives | 22 | 22 |
| Embedded images | 12 | 12, identical payload bytes |
| GLB bytes | 17,036,264 | 17,017,068 |
| Khronos validator errors / warnings | 0 / 0 | 0 / 0 |

The 322-vertex and 19,196-byte (~0.113%) reductions are too small to justify
runtime replacement. **Retain this as a guarded preflight, not a visual-quality
improvement or measured performance win.** The candidate remains scratch-only;
no game asset, render/import state or source material binding changed.

The preservation oracle compares every present attribute's exact bytes,
component type and normalization in each primitive's oriented triangle
multiset, retaining winding under cyclic rotations. It then reloads the written
GLB and compares normalized scene/node/material/sampler/mesh/primitive data and
embedded image hashes. NodeIO normalization is part of that contract: arbitrary
original GLB JSON fields and binary layouts are not guaranteed. Unsupported
accessor/buffer/image metadata and asset copyright/extras are refused rather
than silently discarded. Separate validator checks still matter; this adapter
is not a complete glTF schema validator.

The six focused test groups pass, including the duplicate-vertex benefit,
UV-seam retention, transparent/skinned/animated/morph rejection, unsupported
extension/external-payload refusal, unsupported-metadata refusal, fresh-output
and same-file/repository/symlink-parent guards. The current courtyard run was
executed and independently checked by the reuse reviewer. The existing Khronos
validator 2.0.0-dev.3.10 found 16 informational messages on each file; zero
errors/warnings is not an artistic acceptance. Node 24.19.0 was used. The local
locked install is about 38 MiB and includes unused image-processing transitive
dependencies (including separately licensed sharp/libvips); no package is
bundled into the native game.

## Evidence, remaining limits and next owner

[art-sources.json](art-sources.json) pins fetched file hashes, examined sections,
failed URL attempts, input images, exact adapter files and measured reports.
Detailed scratch evidence is under `/workspace/scratch/community-reuse/art/`:
`source-files/`, `courtyard-r3/report.json`, `validator-report.json`, and the
retained unpromoted candidates. The initial glTF tag-object raw URLs failed;
the annotated tag was dereferenced and actual commit files/license retrieved.
The report preserves those failed requests instead of counting them as reads.

No Blender export, Rigify generation, Material Maker bake, engine import,
new render, physical-GPU profile or runtime promotion was performed. Source
files were read at the specific sections recorded in the ledger; fetched
large files are not represented as fully reviewed. The existing MikkTSpace,
Khronos validator and meshoptimizer adoption remain in place; this does not
relabel earlier REA work as new visual progress. Root owns roadmap timing and
promotion; face/groom and troop/environment artists own the next visible
quality changes, with independent capture review.
