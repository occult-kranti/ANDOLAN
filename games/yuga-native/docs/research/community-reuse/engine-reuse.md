# Engine and reverse-engineering reuse: one actual authoring adapter

Reviewed 17 October 2026 against native source `7c86cd430e2c878b4f5e6ba1b21f562b73fdc32f`.
Retain Godot 4.6.3, Blender, glTF, the existing MikkTSpace tools and the original
Rama rig. The new adoption is a small **offline animation key-reduction audit**
adapted from Source 2 Viewer's MIT code. It reduces a proposed key set from
**20,989 to 13,230 keys (36.97%)**, while the actual runtime library remains
unchanged. This is optional R9 authoring/storage work; it does not fix R4 foot
contact, improve motion appearance or establish runtime performance.

The [source and execution ledger](engine-sources.json) retains 25 immutable
source/license/doc hashes, reading scopes, exact commands, local source hashes,
numerical receipts and output-guard results. The [tool runbook](../../../tools/reuse-animation/README.md)
and [MIT notice](../../../tools/reuse-animation/NOTICE.md) make this actual reuse
reproducible without a Source 2 client or a new game-engine dependency.

## Sources selected for concrete questions

| Source / immutable commit | Actual evidence and terms | Decision and integration cost |
| --- | --- | --- |
| [morluto/rea](https://github.com/morluto/rea/tree/4f7b5fb6023ce2ec449561782d09e3c7e5ac7c7b), `4f7b5fb6023ce2ec449561782d09e3c7e5ac7c7b` | MIT. Current source still declares 6.5.0. Native docs describe selected function inventories, pseudocode, instructions and provider limitations. | Keep the already qualified local tool and Mikk component runner. Current upstream is 21 commits ahead of the previous `300905c1…` source checkpoint; compare paths/metadata were inspected, not every changed implementation. A matching version string does not identify the installed npm package bytes. No upgrade, fresh decompilation or new commercial input occurred. |
| [ValveResourceFormat / Source 2 Viewer](https://github.com/ValveResourceFormat/ValveResourceFormat/tree/b94b74c5417eceaf0f7ec1ad5bed5ec0bccc32e1), `b94b74c5417eceaf0f7ec1ad5bed5ec0bccc32e1` | Community reverse-engineered Source 2 parser/viewer/exporter, rather than Valve's released engine source. MIT code; README explicitly excludes `Tests/Files` game data. Third-party notices include separate libraries/assets and Esoterica ancestry for animation graphs. | Adopt only the selected exporter key algorithm behind an original Python/Godot audit boundary. No .NET runtime, package graph, Source 2 renderer or asset converter is installed. Full viewer/library import has substantially greater dependency and data-contract cost. |
| [Godot demo projects](https://github.com/godotengine/godot-demo-projects/tree/b761b4cd5718a7118f2c95eb55f181d0a5f004f1), `b761b4cd5718a7118f2c95eb55f181d0a5f004f1` | Official original demos under MIT. Selected IK source and project configuration were read; master targets 4.7, while YUGA uses 4.6.3. The model README identifies its demo robot, but no art is selected or imported. | Study only. Existing native `TwoBoneIK3D`/`FABRIK3D` and the retained local synthetic solver probe already cover the engine facility. Porting an older Node3D demo controller would add a second skeleton owner and migration work without a demonstrated gap. |

The suggested `ValveResourceFormat/io_scene_source2` name returned HTTP404;
an exact-name repository search returned zero items. That bounded lookup is
retained as a discovery failure, not a claim that no Blender importer exists.
No installer or alternative mirror was used. The three resolved source trees
were inspected through ordinary GitHub requests; only selected small files
were downloaded, totaling 301,831 bytes.

The prior [ten-fork REA audit](../REA_REUSE_REFRESH.md) found no useful native
implementation difference. This pass did not repeat a popularity survey or
pretend those historical fork pins were refreshed. A fork becomes a candidate
only when its actual diff solves a named provider/format/ownership problem.

## What was actually reused

Source 2 Viewer's [GltfModelExporter.Anim.cs, lines 686–845](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/b94b74c5417eceaf0f7ec1ad5bed5ec0bccc32e1/ValveResourceFormat/IO/Gltf/GltfModelExporter.Anim.cs#L686)
aligns quaternion signs, measures both spherical and normalized-linear
interpolation error, and selects keys with Ramer–Douglas–Peucker subdivision.
Its complete file SHA-256 is
`47122fb3effe5f7a0eb4a89922002a804d753729eaefb5e03095c045fb2ac803`.
The separate duration rule at lines287–298 prevents a constant first joint
from collapsing a glTF clip's duration. These specific functions supplied the
algorithm; the rest of the exporter was not transplanted.

YUGA's existing builder already removes rest-constant channels and collapses
constant posed channels. Loop clips use **48 intervals per clip**, not 48Hz;
nonloops use `max(16, ceil(length * 60))` intervals. The new opportunity is
bounded reduction of the remaining nonconstant tracks.

The new adapter has three explicit stages:

1. `export-library.gd` uses Godot to read the actual `.tres`, preserving its
   clip names, durations, loop modes, paths, key times and values in an external
   JSON extraction. It refuses existing output, symlink components and output
   inside the repository.
2. `audit.py` adapts the MIT algorithm, admits only finite enabled linear
   position/rotation channels and unit transitions, preserves both existing
   endpoints, and uses half the configured error budget for initial selection.
   It restores original neighboring keys when intermediate probes expose a
   missed excursion. Output is a fresh external JSON proposal, not a playable
   Godot resource. Event/method/scale/cubic/partial-span tracks are refused.
3. `verify-candidate.gd` rebuilds the proposed animations **in memory** and
   compares actual Godot interpolation across the original intervals and both
   sides of loop boundaries. Unique, complete source clip-name coverage is
   required. It writes no animation resource or mesh.

No Esoterica code is copied through this adapter. The full MIT copyright and
permission notice accompany the selected VRF adaptation. Code permissions,
converter dependencies and input-game artwork rights remain separate.

## Actual measurement and counterexamples

Input: `assets/animations/rama_hero_motion.tres`, SHA-256
`1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8`.
The extractor read 23 clips and 1,185 tracks from the existing imported project.
The same hash remained after all measurements.

| Check actually run | Result | Boundary |
| --- | --- | --- |
| Python algorithm/admission suite | 10/10 test methods pass, including antipodal quaternions, wide rotations, translation/rotation excursions, endpoints/duration, unsupported tracks and malformed values. Independent reviewer repeated 10/10. | Numerical logic and refusal cases, not visual acceptance. |
| Python original/proposal comparison | 160,227 finite probes; 20,989→13,230 keys. Largest rotation error `0.0000871288123` radians (about0.004992°); largest position error `0.00000486133`m (about0.004861mm). | Both SLERP and normalized-LERP checked. Eight subdivisions per original interval are finite sampling, not a continuous proof. |
| Godot4.6.3 in-memory comparison | 182,246 probes pass, including both sides of loop boundaries. Largest rotation error `0.0000870950977` radians; largest position error `0.00000486085`m. Exact23-name coverage and original durations/loop modes retained. | Actual engine interpolation only; no skeleton skinning, gameplay session or render. |
| Output/path refusal calls | Existing JSON sentinel unchanged; symlink parent rejected before writing. Both exit2 as intended. | Prevents the tested accidental overwrite/path cases. |
| Candidate coverage refusal calls | Duplicate clip names and an unknown clip name both rejected with exit2. | Prevents a passing count from disguising missing clip coverage. |
| Track-contract refusal calls | Mutated kind, interpolation, loop-wrap, enabled state and transition values each rejected with exit2. | Numeric samples do not substitute for preserving source track semantics. |

A meaningful failing test improved the implementation: keys on an exact
SLERP arc can satisfy original-key tests while normalized LERP exceeds the
budget between them. Restoring both source neighbors of the worst dense probe
corrected that case. The real Rama proposal required no such restored keys at
the conservative default budget. An initial GDScript type-inference parse
failure was corrected before successful extraction. Independent review also
caught the original clip-count-only verifier check; exact-name coverage now
has executed negative cases. These are retained limitations/corrections, not
additional successful coverage counted twice.

## Graphics, animation and game-source boundaries

VRF's [format support](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/b94b74c5417eceaf0f7ec1ad5bed5ec0bccc32e1/docs/guides/format-support.md#L152)
describes a useful future interchange path for a specifically permissioned
Source 2 asset. It also records material-layer/PBR approximations, omitted lower
LODs, baked flex weights, additive-animation conventions, no cloth solver in
glTF export and missing physical-property representation. An exported mesh is
not automatically a recreation of the original shader, cloth, facial rig or
gameplay. Animation graphs also depend on runtime parameters and external
slots that compiled data alone may not supply.

The separate [open-game study](../OPEN_GAME_CODE_REUSE.md) retains official TF2
source under its Source1 SDK terms, GPL ioquake3/OpenMW/OpenRA and MIT Godot TPS
code with separately licensed artwork. Those are different origins and reuse
contracts. Their older source studies are not new ports in this pass. A new
renderer/engine migration would discard working Godot/Mikk integration without
solving the current contact, art or native-online acceptance problems.

No Deadlock, Overwatch, Dota2 or TF2 client, map, model, texture, sound or binary
was supplied, downloaded, decompiled or reconstructed here. REA/Ghidra's prior
successful analysis remains the owned compiled Mikk adapter, with its own
separate numerical oracle. This pass neither repeats that tool exercise nor
converts it into a claim about commercial games. No new Reddit content supplied
these selections.

## Next owner and promotion gates

Root owns integration of this optional **R9 offline tool** and its notices.
Keep its candidate outside default assets. Any future resource-writing adapter
must preserve the23 clip names, original timing, loop behavior and authoritative
release receipts, then compare the fully skinned foot/hand/string/aim results
under the actual single-owner motion controller. Follow that with continuous
motion footage and independent review before promotion. Local joint tolerances
can accumulate through a bone hierarchy; they do not bound every vertex or
contact point by the same distance.

There is no measured `.tres`/package byte reduction, frame-time gain or visual
improvement yet. The demonstrated outcome is reusable, attributed authoring
code plus a bounded original-asset measurement. R4 contact quality, native
multiplayer and physical-GPU profiling retain their existing owners and gates.
