# Bounded reuse integration — 23 October 2026

The existing glTF-Transform/meshoptimizer pipeline now has a **separate
required-WebP static source adapter**. Both real generated inputs passed
exact raw-image and oriented per-corner attribute checks. File-size savings
were negligible; neither derivative is promoted to the game.

| Actual input | Source → candidate bytes | Vertices unchanged | Triangles unchanged | Decision |
| --- | ---: | ---: | ---: | --- |
| Generated Rama | 4,480,716 → 4,480,424 (292 saved; 0.0065%) | 93,214 | 96,660 | Keep original; no meaningful size win |
| Generated diya | 3,805,612 → 3,805,276 (336 saved; 0.0088%) | 68,890 | 96,190 | Keep original; no meaningful size win |

This is intake/utility progress. It adds no finished hero, animation, map,
gameplay content or Deadlock-quality acceptance. GPU cost, frame time and
render quality were not measured. Reduced JSON/file bytes do not establish
reduced draw cost or GPU memory.

## What was reused

| Existing resource actually used | Exact identity / role | Rights and limitations |
| --- | --- | --- |
| Project `tools/reuse-art/static-world-preflight.mjs` | SHA-256 `afcd131d66a0ff144efcdb6443c75d98f1dc2ebd66292fc2d5eaf6f6cd01004c`; exact surface oracle, normalized metadata checks and fresh-output policy adapted into a new tool | Private/UNLICENSED project adapter; original file unchanged |
| Existing `tools/reuse-art/package-lock.json` | SHA-256 `1e6fdd8fe4fba0b67d3516e43de3ae4eb96471d4f6acd6b99355ab67cee91793`; existing scratch installation reused, no new install or lock change | Existing full lock/registry-integrity records retained |
| glTF-Transform core/extensions/functions | 4.3.0; existing `NodeIO`, WebP extension support, exact `weld()` and `reorder()` | MIT; source revision `3b3afffbd4d3a29790c9fb166fa4c6755687154d`; [full notice](../../../../tools/reuse-art/NOTICE.md) |
| meshoptimizer | 0.24.0; existing WASM-backed encoder ordering | MIT; source revision `7b2d4f4c817aea55d74dcd65d9763ac2ca608026`; same notice |
| Generated Rama GLB | Original project concept → existing official TRELLIS.2 output; source SHA-256 `0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b` | Existing [source intake and notice](../../../../art/production-stage-oct23/NOTICE.md); service/model/dependency/output terms are not cleared by a utility's MIT license |
| Generated diya GLB | Existing project concept → official TRELLIS.2 output; source SHA-256 `03a9928c489b4b3f2f52ea52c7cbea823eeeaeb082e51d092efb4eef952c966d` | Existing [diya intake notice](../../../../NOTICE/CLOUD-DIYA-PILOT.md); source remains unpromoted |
| Node/Python standard libraries | Existing Node 24.19.0 and Python; tests, exact hashes and independent raw pair oracle | No additional Python package, model or art download |

No imported Deadlock, Overwatch, Dota 2 or TF2 client code, character, map,
texture, rig, effect or animation is present in this integration. No REA,
Ghidra, binary extraction, game installation or broad repo clone was executed.
This task reuses verified available utility code and project assets; it is
not a claim of reverse-engineering either commercial game.

## Contract and verification

[The tool and commands](../../../../tools/reuse-art-next/README.md) use the
canonical lock and explicit installed dependency root. It permits bounded
embedded static triangles, PNG/JPEG and required `EXT_texture_webp` images.
Unknown, undeclared and misplaced extensions, URI resources, malformed ranges
and unsupported provenance metadata are refused before output creation.
Skins, animation and morph targets are rejected intact. A future rigged
asset needs its own tested preservation contract.

The adapter verifies all oriented triangles, including all vertex attributes,
UV seams and winding, before and after exact welding/index ordering. Raw
embedded-image byte hashes/counts/MIME, including publisher padding, must
match. Metadata is compared **after NodeIO normalization**: PBR defaults can
be omitted and an explicit repeat sampler can be emitted. JSON metadata and
the whole GLB are not byte-exact copies. Exact source GLBs stay unchanged.

The first source attempt rejected Rama's second WebP image because its
33,048-byte bufferView contains a 33,046-byte RIFF plus two padding spaces.
[The retained refusal](initial-padding-refusal.json) records that finding.
The narrow correction accepts at most three trailing zero/space bytes and
keeps every byte; it does not trim, transcode or repair the image.

[15 executed Node tests](tests.stdout.txt) passed, including UV seam and
winding controls, declared extension requirements, malformed counts, external
URI refusal with a fetch spy, nonfinite attributes, source immutability,
metadata refusal, fresh outside-checkout paths and dependency-lock mismatch.
[The independent raw Rama](rama-raw-audit.json) and [diya](diya-raw-audit.json)
checks read both GLBs without NodeIO and passed image/triangle identity.
The tests do not claim full glTF validator coverage, a rendering review or a
physical-GPU benchmark.

## Actual stages and retained evidence

The five stages below are this tool's bounded R1–R5 sequence, not five game
quality rounds or a count toward the requested finished game.

1. R1 mapped the existing adapter, lock, installed modules and source rights.
2. R2 implemented a separate extension-aware static preservation contract.
3. R3 ran both actual generated source models with fresh scratch outputs.
4. R4 passed 15 adverse/control tests and two independent raw-pair audits.
5. R5 retained the tool, exact reports, source/module hashes, notices and next gates.

[execution.json](execution.json) binds current tool/test/source hashes,
versions, unchanged canonical files and stage outcomes. [Rama](rama-report.json)
and [diya](diya-report.json) reports contain all four loaded module hashes,
raw image payload hashes, oriented surface identities and elapsed tool time.
Candidate GLBs remain only under:

```text
/workspace/scratch/ten-rounds-oct23/reuse/rama-freeze/candidate.glb
/workspace/scratch/ten-rounds-oct23/reuse/diya-freeze/candidate.glb
```

The exact existing dependency installation is
`/workspace/scratch/production-reuse-oct23/reuse-art-tool/`.
The selected lock and direct versions match; loaded entry hashes are recorded.
This is not an independent integrity audit of every installed transitive file.

Next: keep these originals and complete the artist-controlled topology,
hair/face/material and rig/deformation gates. Attempt a real LOD only after
art acceptance, with silhouette/UV/rig checks and measured cost. Reordering
may improve cache behavior in some engines, but these candidates need target
GPU measurement before any such benefit can be claimed. Do not promote them
solely to save a few hundred file bytes.

The bounded followup [rig R2 code review](RIG_R2_REVIEW.md) separately records
remaining anatomy, shoulder-boundary and REST/export gates for another owner's
failed transfer candidate. It edits no rig code and grants no promotion.
