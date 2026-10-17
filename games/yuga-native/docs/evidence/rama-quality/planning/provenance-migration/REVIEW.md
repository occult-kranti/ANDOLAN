# Authoring provenance and native-content migration

Role 15, checkpoint 3 technical preparation; baseline
`1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`. Root approved this bounded source
change. [Summary](summary.json) records exact owned-file hashes and limits.

The provenance suite passes **118/118**, retaining the nineteen historical cases
and all ninety-one preceding authoring/pose-data/helper cases. The final update
also pins the reviewed face export and its original metadata/generator before
the bounded tangent repair. The retained pure Godot 4.6.3 contract suite passes
**242/242**, without engine errors or
warnings, using two-CPU affinity and isolated user directories. It performs no
import, render, socket operation, live migration or gameplay simulation.
The desk did not edit the active runtime GLB or NOTICE. The original schema-1
contract remains covered by its nineteen preserved cases; root owns promotion.

## Schema 2 contract for root's NOTICE writer

Use [the prepared final template](RAMA-HERO-PROVENANCE.schema2.template.json).
Its terminal face/output hashes and byte count now name the frozen repaired
`de61dc4c…` export, metadata `4fa93bd6…`, native generator `c1a92261…` and unchanged
editable `c541b2bf…`. [Actual fixed authoring files validate](prepared-final-notice-validation.json)
as twenty-three source records in an isolated copied source view. The desk did
not alter the active asset/NOTICE; root owns promotion and actual-project repeat.
Do not add the old flat `generator`, `weightCorrection*` or
`generatedDependencies` fields to schema 2. Generators and dependencies belong
to the exact ordered authoring stage that used them.

| Stage | Required stored output / editable | Generator / metadata / dependencies |
| --- | --- | --- |
| `r7` | `art/hero-rama/history/r7-runtime/rama-hero.glb`; original `art/hero-rama/rama-hero.blend` | Original `build_hero.py`; exact archived schema-1 NOTICE at `art/hero-rama/history/r7-runtime/RAMA-HERO-PROVENANCE.json`; both `rebind_dhoti.py` and `weight-correction.json`. The historical validator still checks its original five identities and original generated-dependency ledger. |
| `q3` | `art/hero-rama-quality/rama-hero-quality.glb` / `.blend` | `build_quality.py`; `provenance.json`; imported original `art/hero-rama/build_hero.py` as an explicit dependency. Metadata must agree with the R7 GLB/editable ancestry and its own output/editable/generator. |
| `face` | `art/hero-rama-face/rama-hero-face.glb` / `.blend` | `build_native_face.py`; `candidate.json`; exactly four dependencies: imported `build_face.py` helper, two pinned `sources/face-poseunits.json` / `.bvh` inputs and `history/r4f-reviewed-before-tangents.glb`. Metadata must agree with Q3's editable input and the reviewed face → repaired output/editable/generator chain. |

Root preserved the original R7 GLB and exact original NOTICE before promotion.
The preserved NOTICE in this evidence directory is a recovery fixture, not the
runtime archive path. Retain the original R7 generator, correction and editable
sources. The final face GLB is copied byte-for-byte to
`assets/heroes/rama-hero.glb`; the top-level editable path/hash must equal the
terminal stage. A parent hash records ancestry; it does not claim a companion
GLB was read as the generator's editable input.

The face stage requires `sourceLedger` / `sourceLedgerSha256` for
`art/hero-rama-face/sources/source-ledger.json` and `licenseNotice` /
`licenseNoticeSha256` for `art/hero-rama-face/NOTICE.md`. Its two pose-data
dependencies are pinned to MakeHuman revision
`a8bc2d54ff0ac92e78ff71431b1023eda42bf482`:

- JSON: 1,590 bytes,
  `e7224f76e9610049b79e5f9e8ac2985d1e9a367333395c07537919258cb42cc3`.
- BVH: 310,826 bytes,
  `42a8e69692e30010371ee6993a6e5d3b468d35065559ec0953c936e31b8d903f`.

The validator checks the fixed source ledger's repository, revision, CC0 license
and exact two file records, actual pinned data bytes, and retained attribution.
Self-hashing replacement data or rewriting the ledger does not bypass these
pins. No MakeHuman application code is imported by this change.

The historical `build_face.py` entry authored the rejected R3 overlay. The proper
face entry imports four shared helpers from that file; it does not call the old
overlay author/export. Preserve the helper and pin its frozen bytes explicitly.
It cannot be relabeled as the terminal generator. The helper counterexamples
retain that distinction and challenge an omitted/changed code helper.

### Exact reviewed face → three-tangent repair

The fourth dependency is the preserved reviewed export
`art/hero-rama-face/history/r4f-reviewed-before-tangents.glb`: **34,322,216 bytes**,
SHA-256 `1fdb01ccb894004a618a594cb41b2e955810c7bdc76855c42f7ce19b0516d92b`.
Its actual input identity is pinned independently of the declared dependency
hash, so self-hashing a replacement does not bypass the gate.

The face stage also declares fixed `reviewedMetadata` / `reviewedMetadataSha256`
for `art/hero-rama-face/history/r4f-reviewed/candidate.json` and
`reviewedGenerator` / `reviewedGeneratorSha256` for that directory's original
`build_native_face.py`. The original geometry generator remains
`f872fa0da92d23a5f03866288c099c9bf7de29f99415b9fd3888d56a6452d036`.
Archived metadata must match Q3's editable input, the reviewed GLB, unchanged
face editable and original generator. Final metadata must retain that
`nativeGeometryGeneratorSha256` and identify its current
`postExportProcessorSha256`. These two provenance records are separate from
the exactly four generated dependencies.

The real repair command reads those records and a copy of the reviewed GLB;
it does not re-export a freshly generated Blender scene. The
[owner's actual byte receipt](../../face/tangent-repair/receipt.json) records
**37 changed bytes within three 16-byte Ivory-silk TANGENT records**. Source and
result are `1fdb01cc…` → `de61dc4c…`; the editable remains `c541b2bf…`.
The validator cross-checks `zeroTangentRepair` source/result identity, exactly
three records, a changed-byte count in 1–48, and the retained unchanged-data
claims. This is metadata consistency, not an independent recomputation of the
byte diff or visual quality. Actual geometry/face-payload identity and the
transfer of prior frame review belong to the linked receipt and independent QA.

The [118-case report](schema2-final-tangent-ancestry-regression.json) adds
missing/unsafe/self-hashed reviewed-input cases, metadata/generator ancestry
contradictions and repair-proof contradictions. The intermediate 104-case
report remains separate. Synthetic package fixtures use a copied, hash-pinned
reviewed input, and do not mutate real art or claim valid GLB/visual acceptance.

Every active/staged source, editable, generator, metadata and dependency must be
present, safe and hash-matched. Ordered stages, exact parent/editable links,
terminal identity and dependency completeness are checked. The export's existing
before/after provenance comparison now covers the whole recorded authoring
chain. These are identity/availability checks, not proof of likeness, a
deterministic rebuild, skin deformation or art quality.

## Native content revision 4

Only native offline content advances **3 → 4**. Browser/proposal content remains
1, every wire/envelope/schema version remains 1, and no live transport adoption
or server migration is claimed. The catalog, pure validator and expected
revision checks have been updated. The old catalog bytes and actual Godot-derived
revision-3 descriptor are preserved in `tests/fixtures/contracts/` and this
directory. Existing revision-1/2 rejection cases remain; new cases prove
revision-3 open/resume/migrate/replay rejection is transactional and changing
only the revision number cannot forge source identity.

The historical pre-freeze source-pin check **failed three pending-freeze checks**:
the changed `player.gd`, changed `rama_hero_runtime.gd`, and the missing required
`rama_action_buffer.gd` pin. That report is retained as evidence of the earlier
blocked state. After root's explicit final source freeze, the desk retained all
fourteen existing rules sources, added the buffer as source fifteen, refreshed
the two changed source hashes and recomputed the compact sorted string-map
content aggregate. The final source-pin check passes **42/42**; the same tree
passes **242/242** pure Godot contract cases, **118/118** provenance
counterexamples and actual canonical-NOTICE validation of **23** source records.
Exact final catalog, sources and reports are archived in
[`../final-native-contracts/`](../final-native-contracts/README.md).
PBR, face, FX and LOD are presentation resources; their full runtime
manifest belongs separately and they are not added to gameplay-rule pins.

The old native revision-3 `rules_sha256` is
`81350321554767054e16de46e2b3f6a0fae7662923b30ccc76f0cfcb2cbe1a9f`.
An initial Python serialization projected a different rules hash; the actual
Godot derivation caught that failure. The failed projection, reports and the
subsequent decoded-number comparison finding are preserved in `history/`.
Descriptor checks use the existing compatibility function's integer-value
semantics for JSON `3.0` versus constructed integer `3`; exact digest strings
still have to match. Do not reuse a Python-serialized full profile hash as an
executed Godot descriptor. The content aggregate contains strings only and is
checked independently by both existing implementations.

## Next owner and remaining gates

Root owns asset/NOTICE promotion, runtime integration and shared source/evidence
manifests. The final pure source/provenance/contract repeat is complete in the
separate final archive. Actual gameplay/render/package checks and the complete
quality runner remain separate gates owned by root. These technical passes do
not establish production art acceptance, native online matches, full roster or
physical-GPU performance.
