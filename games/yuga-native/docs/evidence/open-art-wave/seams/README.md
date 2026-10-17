# Exact corner split checkpoint

`actual-candidate.json` records the scratch-only candidate produced by
`art/hero-rama-repair/split_seams.py`. The input is the separately reviewed
shader-specific mesh-removal candidate `47cd393b…`, not the playable asset.
The output is `5fc60979…`, 47,956,392 bytes.

Six source vertices contain multiple valid official Mikk corner directions.
They need eleven copies: one bow-gem, six hair and four gold records. The
splitter partitions those corner groups without changing any tangent value.
Every base attribute and every morph channel is copied exactly. Source BIN,
accessors and buffer views remain intact as a prefix; materials, images, one
164-joint skin, nine embedded clips and the unique RamaFace are preserved.
Fresh native calls confirm that every corner frame and validity mask is
unchanged, while conflicts at each new source index fall from six to zero.

This prepares topology for a later tangent rebake. It does not improve the
appearance yet. The 144 geometry-degenerate faces, 17,512 UV-degenerate faces,
three zero-output clean corners and 1,170 unused vertices remain explicitly
unresolved. A native importer could merge identical stored vertex records;
no runtime benefit is claimed before a separately reviewed tangent rebake and
native import. The append-only authoring candidate also grows by 11.56 MB;
delivery compaction and runtime memory remain separate work.

Reproduce offline using Python, pinned NumPy 2.3.5 and a C99 compiler:

```sh
python3 games/yuga-native/tests/hero_seam_cases.py \
  --report=/absolute/fresh/seam-tests.json
python3 games/yuga-native/art/hero-rama-repair/split_seams.py \
  --source=/absolute/reviewed-mesh-candidate.glb \
  --library=/absolute/mikk-build/libyuga_mikktspace.so \
  --output=/absolute/fresh/rama-seams.glb \
  --report=/absolute/fresh/seam-report.json
```

The suite has 30 passing checks, including shared accessors, extra UV channels,
sparse and tangent morphs, original tangent preservation, malformed counts,
source aliases, unresolved corners and no-op behavior. It builds the unchanged
official vendored Mikk implementation in a temporary directory by default;
`--build-dir=/absolute/fresh/cache` retains that build. No network, Blender,
Godot import, render or runtime promotion is involved.
