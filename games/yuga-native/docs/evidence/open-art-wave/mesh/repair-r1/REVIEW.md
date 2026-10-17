# Role 01 — offline persistent mesh-pair repair

Status: **structural candidate PASS; no runtime promotion or art acceptance**.
Source commit `a9dd94d8580e72cc109e8c271eb338a471611bfc` plus the exact new
source snapshots in `source/`; complete commands, wall times and hashes are in
`run-receipt.json`. Every executed process exited 0. The test process completed
24 tests; strict/secondary authoring stderr is empty. Unit test progress is
written to stderr by unittest and ends in `OK`, with no warnings or errors.

| Actual source-bound run | Before faces | After faces | Removed |
| --- | ---: | ---: | ---: |
| Default strict all-record pair proof | 408,316 | 408,316 | 0 |
| Pinned `yuga-secondary-v1` experiment | 408,316 | 403,060 | 5,256 |

The strict candidate is byte-identical to source SHA
`de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`.
The experiment candidate is
`/workspace/scratch/rama-mesh-repair-r2/rama-secondary.glb`, SHA
`47cd393b975a9b505216a6051e0376a3020724a8c3400afc7422471dfbd9423d`,
36,398,424 bytes. The source is 34,322,216 bytes; append-only indices deliberately
retain old unused index storage. This is not file-size optimization.

The mesh/script/shader pins are independently recorded in the JSON report.
The public opt-in authoring API refuses a different source or shader hash.
The inspected shader changes vertex position only through a squared clamped
COLOR alpha mask after core skin deformation. The proof requires exact equality
of POSITION, every JOINTS/WEIGHTS set, every POSITION morph and every COLOR
record. All 5,256 core pair proofs also pass COLOR equality. The stronger default
requires all records, including UV/NORMAL/TANGENT and all morph channels; these
seam differences explain its conservative no-op result. The proof does not
apply to unknown custom or vertex-ID-dependent deformation.

Removed faces by source primitive:

| Mesh | Primitive | Removed faces |
| ---: | ---: | ---: |
| 0 | 1 | 400 |
| 2 | 0 | 1,496 |
| 2 | 1 | 336 |
| 2 | 2 | 2,000 |
| 2 | 5 | 168 |
| 2 | 6 | 312 |
| 2 | 7 | 160 |
| 2 | 8 | 128 |
| 2 | 9 | 96 |
| 2 | 10 | 160 |

All original BIN bytes are an exact prefix. All old accessor and bufferView
records remain exact. Materials, skins, animations, morphs, images, nodes and
all other non-index document metadata remain exact. Primitive/material
partitions and retained face order remain unchanged. Each changed primitive
references a newly appended unsigned index accessor with checked count/min/max.
No existing shared index accessor is mutated. Every selected candidate index is
independently compared with its expected retained source index.

The scale-relative float64 geometry diagnostic reports 5,292 computed-zero and
108 additional near-flat-but-positive faces before repair. After repair it
reports **36 computed-zero plus the same 108 positive near-flat faces**.
Neither category is deleted without an exact pair proof. TEXCOORD_0 exact-zero
UV faces go from 18,360 to 17,512 only because some removed 3D-degenerate faces
also had degenerate UVs. The 17,512 remaining UV-degenerate faces are retained;
the tool does not repair UVs or tangent conflicts.

The tests exercise all unsigned index widths/minmax, primitive/material/shared
accessor boundaries, exact non-index preservation, sparse position morphs,
interleaved buffers, normalized integer weights, additional skin/color sets,
tiny real geometry over three scales, no-op/idempotence, empty-primitive refusal,
fresh file/alias/symlink/hardlink guards, corrupt chunks/JSON, nonfinite data,
unsupported storage/extensions and source/shader pin refusal. Independent
linear-algebra oracles show coincident bind-pose vertices becoming visible under
different joint transforms, POSITION morph deltas and secondary alpha masks;
the relevant proof rejects them. Normal/UV/tangent seams stay protected by the
strict policy and are allowed only by the explicitly pinned experiment.

Source snapshots make the executed contract recoverable. The large candidate
remains in scratch and can be regenerated with fresh output names using the
recorded command. Earlier exploratory scratch reports in
`/workspace/scratch/rama-mesh-repair-r1/` remain intact; `repair-r1/` here archives
the final r2 source/command runs, not those earlier diagnostics.

Next gates belong to the independent mesh/deformation and UV/tangent reviewers.
No Blender/Godot import, renderer, posed hero visual check, GPU timing, online
integration or human art acceptance was run. Remaining near-flat topology,
UV-degenerate domains and conflicting tangent frames require authored work.
The runtime GLB remains unchanged.
