# Independent deformation and complete-row review

Role 09 independently reviewed the frozen mesh repair and seam preparation.
The final standalone test passes **26/26 synthetic checks**; the run on the
actual three-file authoring chain passes **38/38 checks, including those same
26**. These are CPU data checks, with no engine import, native Mikk execution,
render or asset promotion.

| Input | SHA-256 |
| --- | --- |
| Reviewed runtime source | `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5` |
| Repair candidate | `47cd393b975a9b505216a6051e0376a3020724a8c3400afc7422471dfbd9423d` |
| Seam candidate | `5fc60979b7e258144e01a5ffb46752c263635e848c983cbd24aad52c5827c792` |
| Reviewed secondary shader | `c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7` |

The actual GLB has **nine embedded animations**, one 164-joint skin and 17
embedded images. The separate runtime motion library's 23 states are outside
this GLB audit. All nine embedded animation records and sampler payloads, skin
records and inverse bind matrices, image bytes, nodes, material partitions,
mesh/morph metadata and original BIN/accessor/view prefixes are preserved.

An independent packed-record selector derives the repair's exact ordered
403,060 retained faces and 5,256 removals from the 408,316-face source. It checks
18 primitive domains, 139 base attribute channels and eight morph channels.
The seam audit independently derives each new vertex's original corner lineage
from the ordered index pairs. All original and cloned attribute/morph records,
including COLOR, skin and original tangents, match their source rows exactly.
Accessor interpretation metadata is checked as well: identical bytes with a
different normalization flag fail. There are 11 clones, 234,846 original rows
and 234,857 candidate rows in total. All 1,170 unused source vertices remain;
this is neither compaction nor a smaller delivery asset.

The position proof is narrow. Equal POSITION, all JOINTS/WEIGHTS sets, every
position-morph delta and full COLOR records give the same position under core
glTF morph/linear skin blending and the exact shader's post-skin
`secondary_offset * clamp(COLOR.a, 0, 1)^2`. A coincident pair then remains
coincident. Uniforms are common within the primitive. This excludes unknown
vertex-ID effects, external deformation and changed shaders. The default
strict authoring policy still compares every attribute and morph channel.
The opt-in public entry rejects a synthetic source with an unapproved custom
displacement attribute before it can use the reduced signature.

Independent calculations demonstrate why bind-pose flatness is insufficient:
different joint IDs or weights, a second skin set, any position morph, or a
secondary alpha mask can open a zero-area triangle. Three distinct collinear
vertices can also open under the inspected shader. Tiny positive geometry and
UV-degenerate but nonzero geometry remain. Full RGB and additional COLOR sets
remain conservatively significant even where this shader does not use them.
Sixty-four seeded mixed affine/morph/secondary samples corroborate the equal
driver invariant; they are not an animation playthrough or a universal proof
for arbitrary shaders.

Counterexamples also prove that the independent conservation checker rejects
changed rig/animation/image data and corrupted appended position, weights and
original tangent rows. This actual seam candidate clones **no morph-bearing
primitive**. Three cloned morph semantics are therefore exercised in an
explicit synthetic decoded-data fixture, with separate corruption negatives,
rather than presented as actual candidate coverage. The initial R2 test draft
incorrectly expected such an actual fixture; its failed receipt is preserved
and superseded by the final reports. R1/R3 are historical test revisions, not
additional unique case counts.

Run the portable synthetic checks from the repository root:

```sh
taskset -c 0,1 env OPENBLAS_NUM_THREADS=1 python3 \
  games/yuga-native/tests/hero_deformation_proof_cases.py \
  --report /absolute/fresh/deformation.json
```

The optional `--source`, `--repair-candidate` and `--seam-candidate` arguments
add the actual artifact comparison. See `summary.json` for the executed full
command, input identities and counts, and `actual-report.json` for each check.
The source snapshots in `source/` pin the reviewed bytes. External candidates
are recorded by path/hash and are not duplicated into this evidence folder.

Remaining UV degeneracy, tangent-frame quality, shading, posed visual quality,
continuous animation, physical GPU timing and delivery budgets still require
their own gates. This review authorizes no runtime asset change.
