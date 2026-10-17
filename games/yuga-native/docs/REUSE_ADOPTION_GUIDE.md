# Reuse guide: tools that build this hero

This pass retains Godot 4.6.3, Blender 4.3.2 and glTF. It adds one actual
upstream authoring algorithm and a reusable native-analysis runner. It does not
replace the engine or claim recovery of Deadlock, Overwatch or Dota 2.

| Resource | Decision and implemented result | Evidence / next use |
| --- | --- | --- |
| Official MikkTSpace, pinned `3e895b49…` | Adopted unmodified permissive C source behind an original bounded adapter. Offline per-corner frames; strict indexed candidates refuse unresolved corners instead of averaging them. | [Tool and commands](../art/hero-rama-tangents/README.md), [notice](../NOTICE/MIKKTSPACE-AUTHORING.md), [actual diagnostic](evidence/reuse-study/mikktspace/summary.json). |
| REA 6.5.0 + Ghidra 12.1.4 | Restored and exercised on the actual compiled Mikk adapter. The generic runner checks the ELF identity, selected symbol and provider, and terminates its owned process group on timeout. | [Runbook](../tools/native-analysis/README.md), [fresh analysis](evidence/reuse-study/rea/native-component/summary.json). Numerical execution remains necessary: decompiler pseudocode obscured finite-value guards. |
| REA upstream and ten forks | Reviewed current upstream plus eight newest and two historical forks. The eight newest had no code divergence; the two others supplied no relevant native-analysis improvement. Retain upstream. | [Exact sources and reading limits](research/REA_REUSE_REFRESH.md). Installed npm package identity and Git source revision are recorded separately. |
| Godot TPS and platformer demos | Study same-engine ownership, sockets and movement contracts. Demo scripts target a newer engine; they are not wholesale imported or runtime-qualified for 4.6.3 here. | [Five-repository audit](research/OPEN_GAME_CODE_REUSE.md), [design notes](research/GAME_DESIGN_REUSE_NOTES.md). MIT code and separately licensed art are distinct. |
| OpenMW / ioquake3 / OpenRA | Behavior studies; no runtime import. The isolated GPL OpenMW pool test demonstrated retained payload and no capacity bound. Retain YUGA's explicit caps and resets. | [Isolated sanitizer execution](evidence/reuse-study/games/module-check/NOTICE.md), [independent review](evidence/reuse-study/qa/game-reuse-source-review.json). Research GPL source stays isolated with its license. |
| Official TF2 Source SDK | Study camera/grapple behavior under its restricted mod license. No copied SDK code, maps, models or effects enter YUGA. | [Source/license audit](research/OPEN_GAME_CODE_REUSE.md); earlier [TF2 study](research/TF2_REUSE_STUDY.md). |
| Nystrom, *Game Programming Patterns* | Selected sections of four chapters, including new Component/Update Method reading. Eight explicit implementation gates cover timing, ownership, pooling, warnings, minions, LOD, camera and input/reset. | [Notes and exact reading scope](research/GAME_DESIGN_REUSE_NOTES.md). This is not a claim to have read all books or tested all eight production gates. |

## The actual blocker and the next implementation

On the selected near Rama asset `de61dc4c…`, the strict tangent-only candidate
was refused; no replacement GLB was written. There are 5,400 geometry-degenerate
and 18,360 UV-degenerate faces, with 22,912 in their union under the documented
epsilon. There are also three invalid corner outputs on otherwise clean faces,
six indexed direction conflicts, and no shared-index handedness conflict.
68,739 unresolved **corners** must not be described as 22,913 unresolved faces.

The [next fifteen assignments](OPEN_ART_WAVE.md) implement conservative mesh
repair, better authoring diagnostics, selected open art, reproducible tooling
and matched native comparisons. A zero-area bind-pose triangle may become
visible under skinning; removal requires persistent deformation equivalence.
Changing a UV chart also requires its associated normal-map/material review.
Candidate assets stay outside the runtime until independent structural and
actual-image checks support promotion.

## Reproduce the bounded checks

From the repository root, with Python/NumPy and a C99 compiler:

```sh
python3 games/yuga-native/tests/hero_tangent_cases.py --report=/absolute/fresh/mikk.json
python3 games/yuga-native/tests/native_component_analysis_cases.py --report=/absolute/fresh/analysis.json
```

Both are included in `tools/cloud/setup-native.sh` and native CI. These are
authoring/lifetime checks; they do not establish finished art, client/server
integration, human game feel, listening approval or physical-GPU performance.
The earlier [777-assertion quality integration](RAMA_QUALITY_MILESTONE.md) and
immutable downloadable R7 preview keep their own source identities and scope.
