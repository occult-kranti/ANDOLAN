# Embedded-WebP static source preflight

This separate offline adapter reuses the existing locked glTF-Transform 4.3.0
and meshoptimizer 0.24.0 installation. It extends source intake to required
`EXT_texture_webp`; the canonical `../reuse-art/static-world-preflight.mjs`
and its contract remain unchanged. It is not a runtime asset replacement tool.

From the repository root, use the existing dependency installation:

```sh
npm ci --prefix games/yuga-native/tools/reuse-art --ignore-scripts
node --test games/yuga-native/tools/reuse-art-next/test.mjs
node games/yuga-native/tools/reuse-art-next/webp-static-preflight.mjs \
  games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb \
  /workspace/scratch/rama-webp-preflight
```

The output parent must already exist, be canonical (no symlink parents), and
the output directory must be fresh and outside the repository. No source is
overwritten. No network, decoder download or external-resource fetch is used.

This run reused `/workspace/scratch/production-reuse-oct23/reuse-art-tool/`:

```sh
YUGA_REUSE_DEPENDENCIES=/workspace/scratch/production-reuse-oct23/reuse-art-tool \
  node --test games/yuga-native/tools/reuse-art-next/test.mjs
node games/yuga-native/tools/reuse-art-next/webp-static-preflight.mjs \
  games/yuga-native/art/concepts/cloud-diya-pilot/candidate.glb \
  /workspace/scratch/diya-webp-preflight \
  --dependencies /workspace/scratch/production-reuse-oct23/reuse-art-tool
```

The selected installation must have the canonical lock file byte for byte and
the four direct package versions must match. Reports hash their loaded entry
modules; this checks the selected installation and does not independently
reverify every transitive installed file against npm registry integrity.
Retain the lock and installed license files. See [NOTICE.md](NOTICE.md).

The contract accepts bounded embedded static triangles, PNG/JPEG and required
WebP images. It refuses unknown/undeclared/misplaced extensions, external URIs,
skins, animations, morph targets, transparent BLEND sorting and metadata whose
preservation has not been established. A rigged or animated hero is rejected
intact; no rig or animation is stripped. A general glTF validator and rendered
review remain separate requirements.

Only bitwise identical vertex welding and index/vertex ordering are attempted.
Every corner's attribute bytes and triangle winding must survive, as must
normalized scenes, nodes, materials, sampler and mesh metadata. Full raw
embedded image payloads, including valid trailing publisher padding, must
match input bytes. There is no lossy simplification, quantization, texture
reencoding, normal regeneration, compression extension or image transcode.

An independent Python standard-library oracle reads both raw GLBs without
NodeIO, checking image payloads and oriented per-corner attribute triangles:

```sh
python3 games/yuga-native/tools/reuse-art-next/raw-pair-audit.py \
  SOURCE.glb /absolute/fresh/output/candidate.glb
```

The actual Rama and diya candidates retained the same vertex and triangle
counts, saving only 292 and 336 file bytes respectively. They remain in
scratch. Neither is promoted and no GPU, rendering quality or performance
improvement is claimed. Exact outcomes, commands, source rights and next
gates are in [the reuse handoff](../../docs/research/ten-rounds-oct23/reuse/README.md).
