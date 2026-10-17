# Open art wave: source-bound handoff

Product/task: **native YUGA, NEXT15 roles 01–15**, 17 October 2026.
The bounded authoring, material-fixture and review work is documented below.
The overall art target remains **LIMITED / OPEN**. No candidate mesh or material
has been promoted into the playable game or qualified as a new release.

The source base is `658804fd6e454c6d584ac3245601506b22075c0b`, on
`game/yuga-native-production`. This review covers subsequent uncommitted source
bytes pinned in [the role15 inventory](evidence/open-art-wave/final-review/source-pins.json).
That inventory is a review cut, not a commit, push or updated-source CI receipt.
The moderator reported that the base commit's native CI run
[39060470918](https://github.com/occult-kranti/ANDOLAN/actions/runs/39060470918)
completed successfully; its artifacts were not downloaded for this review.
The moderator owns final source publication. Verify the branch/commit on
[GitHub Actions](https://github.com/occult-kranti/ANDOLAN/actions/workflows/yuga-native.yml)
before a release; a local receipt is not a remote CI conclusion.

## Implemented work and its evidence

| Roles | Result and exact scope | Evidence |
| --- | --- | --- |
| 01, 05 | Conservative repair keeps the strict default byte-identical. The source/shader-pinned experiment removes 5,256 persistent coincident-pair faces while preserving other records. This produces a larger scratch authoring candidate. | [Mesh review](evidence/open-art-wave/mesh/repair-r1/REVIEW.md), [independent contracts](evidence/open-art-wave/qa/contract/REVIEW.md) |
| 02, 13 | Three pinned Microsoft CC0 maps and deterministic derivatives have file-level permission and separate CC-BY metadata attribution. The unsupported repository-wide MIT claim was corrected with an explicit file-scoped grant; the moderator's repeated verifier passed 52/52. | [Material report](evidence/open-art-wave/materials/report.json), [original provenance review](evidence/open-art-wave/provenance/REVIEW.md), [notice correction](evidence/open-art-wave/provenance/notice-correction.json), [52-check repeat](evidence/open-art-wave/provenance/notice-correction-repeat.json) |
| 03 | Exact UV/corner diagnosis separates collinear UVs, real surface area, Mikk corner conflicts and zero frame outputs. Diagnosis changes no UVs or runtime asset. | [UV review](evidence/open-art-wave/uv/README.md) |
| 04 | Locked external REA 6.5.0 bootstrap had an actual fresh npm install plus version/help and 20 bounded guard checks. Its offline dry-run invokes no Node/npm subprocess. No runtime dependency or provider setup is claimed. | [Toolchain summary](evidence/open-art-wave/toolchain/summary.json) |
| 06, 11 | Corrected seam admission/output guards are covered by the owner's 48-check source freeze and the independent 16-check adversarial repeat. A later actual CLI run passed 42 checks, exited 0 with empty stderr and reproduced the same seam candidate hash. | [Corrected seam review](evidence/open-art-wave/seams/R2/README.md), [adversarial repeat](evidence/open-art-wave/adversarial/cases-r2.json), [actual CLI repeat](evidence/open-art-wave/adversarial/actual-seam-cli-r2.json) |
| 07 | Optional R2 surface-only profile preserves authored `base_color`, `base_texture` and `use_base_texture`. Real material ownership/lifecycle runs passed 38 synthetic and 39 actual-resource assertions, native exit 0, with zero recorded error/warning lines. Default game flow is unchanged. | [R2 integration receipt](evidence/open-art-wave/integration/receipt-r2.json) |
| 08, 12 | R1 has eight preserved actual frames and an independent pixel review: LIMITED for exploration, REJECT default promotion because the brighter blue cloth loses authored gold motifs. R2 also has eight preserved actual frames; its optional surface-only profile is independently accepted, while overall art stays LIMITED and default adoption is not approved. | [R1 pixel review](evidence/open-art-wave/visual-review/REVIEW.md), [raw R1 capture](evidence/open-art-wave/render/r1/material-capture.json), [R2 pixel review](evidence/open-art-wave/visual-review/r2/REVIEW.md), [R2 capture](evidence/open-art-wave/render/r2/material-capture.json) |
| 09 | Independent deformation proof passed 26 synthetic checks and 38 with the actual three-file chain, including those same 26. Nine embedded GLB animations, skin/images and cloned records are conserved. | [Deformation review](evidence/open-art-wave/deformation/REVIEW.md) |
| 10 | One ten-suite offline authoring catalog is shared by setup and CI. The runner requires fresh reports, nonempty strict outcomes, native exit 0, no logged errors, bounded process groups and source preservation. The owner passed 33 real process/report boundary cases and 12 syntax/parity checks. The final source-bound catalog passes 259 assertions across all ten suites, including staging, real texture imports and the 39-case material check. | [Runner cases](evidence/open-art-wave/build/runner-cases.json), [syntax/parity](evidence/open-art-wave/build/syntax-and-parity.json), [full ten-suite run](evidence/open-art-wave/build/full-run-r1/summary.json) |
| 14 | Stager copies eight exact cloth dependencies plus a generated minimal project into a fresh external fixture, preserving the product `art/.gdignore`. The owner's 22 tests cover real CLI guards and source preservation. | [Staging review](evidence/open-art-wave/staging/REVIEW.md) |
| 15 | Independent review found and closed a duplicate-JSON false-PASS. Nine further Python probes passed at the fixed source, including process cleanup, unittest outcomes, imports, report guards and actual staging. | [Original finding](evidence/open-art-wave/final-review/runner-duplicate-before-fix.json), [independent closure](evidence/open-art-wave/final-review/runner-review-after-fix.json) |

Counts above describe their own receipts. Historical revisions and overlapping
fixtures are not additional unique coverage. Neither generated counts nor
component passes erase failed runs or establish accepted art.

## Independent runner and stager review

The initial actual exit-zero child emitted contradictory duplicate `passed`
members in both summary and check objects. The previous parser silently kept
the last values and accepted the report. The CI owner introduced `strict_json`,
which rejects duplicate members at every object depth and nonfinite constants,
and applied it to suite reports, material-builder stdout and staging receipts.
Four real child cases extend the previous 29-case suite to 33.

The independent [nine-case script](evidence/open-art-wave/final-review/independent_runner_review.py)
then verified rejection of summary/check duplicates, symlink and oversized
reports; cleanup of an ordinary descendant after its parent exits successfully;
neighboring fixture imports; rejection of expected-failure and unexpected-success
unittest outcomes; and actual byte-identical staging. Product source bytes,
including `art/.gdignore`, stayed unchanged. The temporary fixture had precisely
eight copied dependencies, the generated configuration and its manifest.
No Godot, editor import, renderer or game input ran in this role15 check.

Reviewed runner SHA-256:
`f756914c39a724461db3251d7b543c6c49597c1b6cab7a3e548d69e6eef19062`.
Reviewed stager SHA-256:
`1e8686ed4f35296561f3710ab80d46712c2fcb0421ba6e9a58ddfc79c6b943ef`.
The independently produced closure report is
`cf09a3df8459019bbc2ec43a2af1600206fcd442389c64acee29c2b83b2a398d`.
Process-group cleanup covers ordinary POSIX descendants; it is not an operating
system sandbox. Source envelopes and PNG chunk checks do not replace Godot's
parser/importer. The full actual-resource gate must additionally verify the
three imported texture payloads and the material report/native exit.

## Preserved failures and unresolved defects

- [Adversarial R1](evidence/open-art-wave/adversarial/cases-r1.json) failed on
  a short logical buffer, a nonfinite source tangent and a dangling report
  symlink. The corrected 16-check repeat and 42-check actual repeat above are
  the current closure; the earlier 30-check seam packet remains historical.
- [Integration failures](evidence/open-art-wave/integration/failed-runs.json)
  retain an assertion report followed by cleanup errors/native exit 134, and a
  later import failure whose old outer shell lost the engine status. Neither
  run is accepted. The runner now checks the actual child exit and errors.
- [The failed deformation draft](evidence/open-art-wave/deformation/prototype-r2-missing-fixture.json)
  required a cloned morph channel absent from the actual candidate. The final
  proof exercises cloned morphs in an explicit synthetic fixture instead.
- [The original provenance receipt](evidence/open-art-wave/provenance/receipt-final.json)
  retains the failed repository-wide license assertion. The separate 52-check
  correction repeat closes that specific source claim.
- R1's cloth appearance rejection remains valid for its frozen source and eight
  actual frames. R2's independent pixel decision accepts only the optional surface treatment;
  production-quality and default-adoption gates remain open.
- **17,512 UV-degenerate faces with nonzero surface area, three zero Mikk
  outputs and 1,170 unused vertices remain.** Seam preparation leaves 52,971
  unresolved corners. Its 11 clones remove six index conflicts while preserving
  original tangents; no tangent rebake or UV repair is accepted.
- The seam authoring candidate is 47,956,392 bytes, SHA-256
  `5fc60979b7e258144e01a5ffb46752c263635e848c983cbd24aad52c5827c792`.
  Its append-only size growth is not optimization or a runtime memory win.
  The repair input is `47cd393b975a9b505216a6051e0376a3020724a8c3400afc7422471dfbd9423d`;
  the playable high hero remains `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`.
- Nine embedded GLB clips are distinct from the **23 external runtime motion
  states**. Data conservation does not establish continuous motion/contact,
  expression, authored hair/drape, listening quality or finished materials.

## Next owner and final gates

| Next action | Owner | Status at this cut |
| --- | --- | --- |
| Run the full ten-suite catalog against the final frozen seam/binder/tool bytes; retain exact reports, stdout/stderr, import payloads and native exits. | Role10 / moderator | Complete: 259 assertions / ten suites; exact source pins unchanged. |
| Finish eight actual R2 raw frames, verify source/camera/light/state pins and independently review the preserved-albedo pixels. | Roles08 / 12 / moderator | Complete: eight R2 frames, clean direct exit; optional profile accepted by independent review. |
| Record final source commit, push and the corresponding new-source CI conclusion; repeat final archive/provenance checks. | Moderator | Verify exact published commit in Actions; local archive/source checks belong to this review cut. |
| Author the remaining UV/normal domains, rebake tangents under a reviewed contract, and qualify imported appearance/deformation before any asset promotion. | Next mesh / UV / animation / art owners | Open. |
| Qualify actual packages, physical-GPU timing, native authority/two clients, broader roster and full-game quality. | Production owners | Open; this offline slice does not close these gates. |

Camera placement labels 780/350 are targets; the recorded projected rest AABBs
are 986.35/386.26 pixels. Do not treat those labels as exact measured character heights.

No broad local rerun of unchanged controllers/assets is claimed here. The existing
777-assertion integration milestone and downloadable preview retain their own
source identities. The moderator owns backlog/README/manifests, reusable cloud
configuration and final Git publication. Role15 changed only this handoff and
`docs/evidence/open-art-wave/final-review/`.
