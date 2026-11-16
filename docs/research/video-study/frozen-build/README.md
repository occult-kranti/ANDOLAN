# Frozen native candidate

The corrected candidate is now **snapshot `build-r4/`**. Its
[successor receipt](receipt-r4.json) and [bounded overlay](candidate-overlay-manifest-r4.json)
record the fixed purchase-receipt footer and deferred first-open layout. Only
the panel presentation source changed; authority, Sangam and art are unchanged.
Source checks pass **83/83** and the updated shop-flow guard passes **22/22**.
The unchanged map's **33/33** receipt remains retained rather than relabeled as
a new run.

R4 runtime digest:
`27c18c8e98eb242aeddb228b47ffeece7dd74de0f460867b96d9291c56017c6d`.
Both R4 PCKs have 612 entries, 88,199,444 bytes and SHA-256
`e4e860fc4014f22ef8d67e38df73309c67d5445f6b1221ec625b59480594c8bb`.
Linux ZIP: 115,178,949 bytes,
`b49421501197edf225e9edcf2c2d229ced777c52d53aa33646139df428de998a`.
Windows ZIP: 163,475,846 bytes,
`50b4a974b8762cad3137c44ea109cee0fd646c6bc286b0eb407a0c61c80a16c4`.
All are under `/workspaces/scratch/yuga-video-frozen-r1/build-r4`.
The field shop opens with **F4**. Root owns the final actual-window review.

The R2 checkpoint and its earlier handoff below are preserved. R3 is also
retained; both earlier source states are reconstructable using the saved panel
versions, and their ZIP/PCK bytes remain unchanged.

## Preserved R2 checkpoint

The isolated candidate successfully exports and packages from
`/workspaces/scratch/yuga-video-frozen-r1`. Shared runtime, tools, assets and
earlier failed builds were not changed by this owner. The baseline remains
`work/yuga-studio@7162b5d0b666e4422b0bc73100e1fba947d3323f` with explicit
uncommitted snapshot changes.

The [complete receipt](receipt.json) records commands, exact paths, hashes,
engine provenance and limits. The frozen runtime has 622 files and digest
`e50681013171d1a503c29726ee76a80b9b5b7e85375b110d9e606f1d25cb343f`.
Both PCKs are 88,199,188 bytes with 612 members, SHA-256
`ef299abef23c5ad7a406508f34627725e793c6d097b79d773a8cddc103fce5b9`.

| Artifact, relative to snapshot `build-r2/` | Bytes | SHA-256 |
| --- | ---: | --- |
| `yuga-native-linux-x86_64.zip` | 115,178,667 | `d0d11fb5d4e1d64354a5bd49ff7bf6fba09c0923f0729017df645f6d3a52fbd6` |
| `yuga-native-windows-x86_64.zip` | 163,475,561 | `ffdcce305d3c4e49c2259002c691a088a2c2b97924d205f4ea3ad9f266d5364c` |

`native-export-manifest.json` and `native-package-manifest.json` are beside the
PCK/ZIP files. The original canonical packager verifies every PCK member and
ZIP CRC/payload hash. It uses the official Godot 4.6.3 exporter, reviewed
pipeline-priority public-source Linux runtime and pinned official Windows
runtime, with their original source/build/license proof closure. Windows
execution is unrun.

## Isolation and deliberate candidate difference

The live tree changed during two earlier exports. This owner copied the native
tree, preserved import/UID sidecars, copied the actual import cache separately,
and ran import only in the snapshot. Copying unrelated historical evidence
media was stopped at root's request; already copied data remains. The complete
art tree plus finite Godot and Rama validator dependency closures were retained.
The [copy receipt](bounded-copy.json) and
[additional Rama dependency closure](additional-rama-proof-closure.json) record
that boundary.

The copied tree reproduced a stale Sangam finish-shader pin. At root's explicit
direction, the unmodified current authoring script and shader were copied into
the snapshot and the original Blender authoring job ran with eight threads and
no render. It passed the coplanar audit/assertions and generated the GLB, blend,
specification and manifest. The measured candidate has 308,422 triangles and
26 mesh objects; GLB SHA-256 is
`c29f403d894d183355e785442695f35369b28da57c057be28256ff90c2498a3e`.
Previous copied generation outputs remain under snapshot
`preserved-before-regeneration/`.

Only the copied content10 catalog's two Sangam source pins and content aggregate
were refreshed after that real generation. All 17 revision9 source pins and all
other fields remain unchanged. The candidate can differ from later concurrent
live work: [overlay manifest](candidate-overlay-manifest.json) records both
initial-copy and later-live comparisons, with small text overlays retained.
There is no live writeback.

The copied packager remains exactly the original recorded source
`5f0e17ba903a5415922d6446ec3b01fa26eee55c39f377fa83b81b2b7d0f1cff`.
Later live changes added snapshot-marker support and updated package README
wording; they were not silently substituted. The requested `GIT_DIR`,
`GIT_WORK_TREE` and `GIT_OPTIONAL_LOCKS=0` environment records the actual HEAD,
branch and copied-tree dirty status without creating or committing a worktree.
See [copy identity](canonical-packager-copy-identity.json).

## Checks and remaining owner

The copied source checker passes **83/83**, actual Sangam map/collision tests
pass **33/33**, and actual shop/HUD input-flow tests pass **21/21**. Reports and
logs are `contract-source-r2`, `sangam-cases-r2` and `shop-flow-r2` in this
directory. Source and finite contract inputs remain unchanged after export and
packaging. The initial stale-pin rejection and missing historical Rama helper
export rejection remain preserved with the successful successor.

This owner reviewed source, generated metadata and headless receipts. Root owns
actual native capture/input of this exact PCK and independent package review.
These build checks do not establish finished art, human balance, online matches,
physical-GPU performance or native Windows execution.
