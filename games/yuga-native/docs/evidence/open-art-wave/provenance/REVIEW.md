# Role 13: provenance and package boundary review

Product/task: native YUGA, NEXT15-13. Source commit at review:
`658804fd6e454c6d584ac3245601506b22075c0b`.
This review owns only `docs/evidence/open-art-wave/provenance/`.

The source-image permissions, source pins, deterministic derivatives and
authoring/runtime separation are supported. One notice claim needs correction:
`NOTICE/OPEN-ART-WAVE.md` originally called the generator/resource code subject
to the “repository's MIT license.” At this cut there is no top-level LICENSE
file or package.json license field. Third-party MIT notices do not establish
the repository's license. The moderator was notified; clarify the grant for
these original files or remove the unsupported repository-wide claim. The
verifier checks this separately from the valid third-party permissions.

`receipt-r1.json` is the first 51-check run; it predates this additional finding.
`receipt-final.json` is the later source-bound review cut. Rerun with a fresh
output after any correction; neither receipt is a final whole-wave archive.

| Resource | Exact source and permission | Observed boundary |
| --- | --- | --- |
| Three technicalFabricSmall PNGs | Microsoft 2020 SheenCloth; Khronos revision `edc7c9e67c639d230715049ee31f9a96a6babbbe`; CC0-1.0 | Only three selected 256² images, 384,181 bytes, acquired; source/license manifest pins match actual files. |
| LICENSE.md / metadata.json | Explicit separate CC-BY-4.0 metadocumentation exception | Unchanged original bytes, author/owner fields and license links retained; broad metadata “Everything” does not override LICENSE.md. |
| Three indigo texture derivatives | Original recolor/roughness/normal/repetition adaptation; declared CC0-1.0 | Three 1024² PNGs, 613,976 bytes; original tool `--check` regenerates identical bytes. This is texture provenance, not visual acceptance. |
| MikkTSpace C/header/README | `mmikk/MikkTSpace` revision `3e895b49d05ea07e4c2133156cfa94369e19e409`; upstream zlib-style notices intact | All three upstream hashes verified. Original `bridge.c` is separately marked CC0-1.0. Offline authoring, no runtime references found. |
| REA bootstrap and lock | `rea-agents` exactly 6.5.0, root package MIT; 179 lock entries including root | Manifests only, no newly vendored npm implementation. Install target is outside checkout; dependencies/providers retain their separate terms. Saved role04 fresh-install receipt reports npm ci + version/help; this reviewer did not reinstall it. |
| OpenMW pool experiment | `OpenMW/openmw` revision `fa732a1551a696f8cb52a65c9896b8b4b92eb3dd`; unchanged header plus full GPLv3 COPYING, original GPL-3.0-only harness | Three file hashes match. Isolated research component in docs; no runtime reference found and docs are configured out of exports. No research executable was executed here. |

The complete file-level SHA-256 inventory is in the JSON receipt. Selected pins:

- Source basecolor: `e945c0b2aa6e3987d8bb8af23aca58a3f75cce2992bb4803bec8cac6cde8474e`.
- Source normal: `299b1ccf8957d451d7841672b1750b5cfcea65fee1c97eec6b086dc3fdeea838`.
- Source ORM: `41c04abdb9531d00a4ac832d41f02cd549c7be74886c4d492475cfb95d239a20`.
- LICENSE.md: `8e53964dcfe1d96b58064e4906222a9ef126fa3fc22d8cac59db0542366a915a`.
- metadata.json: `637e75a8a577ae59a62742bb545b32217ef93b24571b6504f8f8313e33adc6be`.
- REA lock: `73fa03d670870e8234e7823bca98e8cd846773fb661819ffe48a5bbb6728c7dd`.
- REA bootstrap: `c20d4fdf0586ee36c8dc4587461c416e780447e83dec4a570c4e9b7eeb19f212`.

The current runtime high Rama remains the 34,322,216-byte GLB
`de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`.
All runtime asset paths were checked for tracked/untracked changes against HEAD;
none were present at the review cut. Mid/far GLBs are separately pinned in the
receipt. The optional material fixture lives under `art/open-art-wave/`; runtime
scripts/scenes/shaders/text resources contain no new authoring dependency
references. No material was promoted into the game by this review.

The actual scratch mesh candidate at
`/workspace/scratch/rama-mesh-repair-r2/rama-secondary.glb` was independently read:
36,398,424 bytes,
`47cd393b975a9b505216a6051e0376a3020724a8c3400afc7422471dfbd9423d`.
It agrees with the retained mesh report and remains outside runtime. This hash
observation does not establish deformation or appearance acceptance. Seam role06
was still being authored when the moderator ended this bounded review; no seam
hash or future seam candidate is accepted here. Root owns its final freeze.

Both export presets use `all_resources` and configure exclusions for `art/*`,
`tools/*`, `docs/*`, `source/*`, `NOTICE/*`, tests and build output. The packaging
helper separately copies all NOTICE files to the portable package directory.
These are inspected source settings. No new Godot export, PCK/ZIP inspection or
package execution was performed, so actual package inclusion/exclusion remains
unqualified. The root's later source archive must retain original image metadata
notices, Mikk source notices and the isolated OpenMW COPYING/NOTICE wherever it
copies those resources.

Executed checks:

```sh
python3 games/yuga-native/docs/evidence/open-art-wave/provenance/verify.py \
  --report /workspace/ANDOLAN/games/yuga-native/docs/evidence/open-art-wave/provenance/receipt-final.json
```

The verifier also executes `build-open-art-materials.py --check` without writes
or network. Its fresh report path and manifest source paths are validated;
manifest inputs must stay within their repository roots. Its sensitive-pattern
scan reports boolean/count data only for changed/untracked nonbinary files up
to 4 MB, covering known GitHub/private-key/AWS/Slack/OpenAI/userinfo patterns.
Ordinary SHA-256 and npm sha512 integrity values are not tokens. A clean bounded
scan does not establish absence of every secret; root must repeat after the
remaining workers and before commit/push. No credential content was retained.

No source/manifest check, CLI receipt, deterministic texture regeneration or
scratch hash is counted as native game quality, human art acceptance, hardware
performance, online readiness or shipped package qualification.
