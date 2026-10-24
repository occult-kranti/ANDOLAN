# Recover the exact source, then make a fresh replay

The unique final editable master and original licensed donor are retained here as deterministic gzip archives. Originals remain in scratch. Compression used level 6, mtime 0 and no filename header; streamed decompression verified the exact bytes before publication. [Compression receipt](source/compression-receipt.json).

| Archive | Archive size / SHA-256 | Exact decompressed source |
| --- | --- | --- |
| [Final editable study](source/rama-mpfb-density-material-study.blend.gz) | 41,328,774 B (39.41 MiB); `fb597331f826bbec3cc35f92f898c0031ca8554c24f992c4e084168af981eb91` | 137,953,532 B; `8cd254da5f789c14a59a1f150ee738fcea556c2c1b9accb3e6193fc45f0b3ace` |
| [Original CC0 donor](source/mpfb-hair-original.blend.gz) | 5,520,227 B (5.26 MiB); `bcdbf3125cd838c6040b438f6bfc14dd6121eac39c97bdd9e9a76e0e41883755` | 19,608,264 B; `93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5` |

Each is below the approved 45 MiB limit. Archival preserves candidate phase; it does not qualify the new hair for native animation or runtime use.

From this packet directory, recover outside the checkout into fresh filenames:

```sh
python3 recover_sources.py --destination /workspace/scratch/recovered-mpfb-hair
```

The helper checks archive hashes, refuses existing destinations, streams decompression and verifies the exact original size/hash. It also writes a path-only copy of the final source receipt so a replay can find the recovered master. Historical source/render receipts remain unchanged. Archive byte verification was executed; this convenience recovery helper was not separately executed in this checkpoint.

The master contains the unchanged approved baseline, the preview-only MASK modifier for the known nine nape components, original guide data, donor Human surface, editable fit transform, material parameter copy, and frozen profile/rear cameras. Open with Blender auto-execution disabled. The explicit `source/compression-receipt.json` is the recovery authority; a rebuild's newly serialized `.blend` need not have an identical byte hash.

For a new actual readiness check, from the repository root:

```sh
blender --background --disable-autoexec --threads 1 --python-exit-code 1 \
  --python games/yuga-native/docs/research/reuse-next-ten/reuse-advisor-hero/evaluated_probe.py -- \
  --receipt /workspace/scratch/recovered-mpfb-hair/relocated-refined-source.json \
  --output /workspace/scratch/recovered-mpfb-hair/new-evaluated-probe.json
```

Only after that actual gate and the shared heavy-render lease are available, a fresh two-view replay can use:

```sh
timeout 300s blender --background --disable-autoexec --threads 2 --python-exit-code 1 \
  --python games/yuga-native/docs/research/reuse-next-ten/reuse-advisor-hero/render_preview.py -- \
  --receipt /workspace/scratch/recovered-mpfb-hair/relocated-refined-source.json \
  --eligibility /workspace/scratch/recovered-mpfb-hair/new-evaluated-probe.json \
  --comparison-receipt games/yuga-native/docs/research/reuse-next-ten/reuse-advisor-hero/evidence/initial-render.json \
  --output /workspace/scratch/recovered-mpfb-hair/new-two-view-capture
```

This produces new evidence, not the already-reviewed originals. The renderer requires nonempty/finite bounded actual geometry, ≤20,000 curves and ≤1,300,000 points before any frame, and checks camera identity against the retained baseline. No canonical model or GLB is written.

For authoring reconstruction instead of exact recovery, `fit_preview.py` consumes the original donor plus the approved Rama source master SHA `30b44c96…` and the unchanged old-nape region receipt. Those prior inputs remain durably archived in the [R1 packet](../../../../art/reuse-next-heroes/rama-posterior-sculpt-r1/source/MASTER-RECOVERY.md) and [component receipt](../../../../art/reuse-next-heroes/rama-existing-clumps-r2/source/source-receipt.json.gz). `refine_parameters.py` then applies the single recorded density/material change to a fresh fitted scene. The source receipts give exact commands' inputs, selected IDs, transform and parameter values. Rebuilding creates a new serialized scene and requires fresh verification; it is not permission for another uncontrolled parameter sweep.

MPFB installation is unnecessary for the exercised direct-datablock path. The source-code license and the asset license remain distinct; read [NOTICE.md](NOTICE.md) before reusing or redistributing upstream program code.
