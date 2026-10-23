# Independent review · 23 October 2026

This review is scoped to the reuse-first continuation from source
`067ad5d5e12b4de71d75b658aa511beb8f175fc9`. The lead owns integration,
the ten-stage ledger, CI and publication. This packet awards no finished-game,
commercial-art, hardware or Android completion credit.

| Claim | Decision | Evidence and limit |
| --- | --- | --- |
| Raw generated source understood | Accepted for diagnosis | [Raw GLB audit](source-glb-audit.json): 93,214 split vertices, 45,565 exact positions, 96,660 triangles, 20 components, zero exact-position boundary edges and 1,570 edges with incidence above two. This does not qualify the art or rig. |
| Conservative rear-hair cleanup | Rejected for art | [Independent byte/image review](cleanup-independent.json): eligibility passes, front stays stable, rear pits and smeared flow remain. Five actual locked CPU renders inspected. |
| Initial nearest-surface rig transfer and one correction | Rejected | [R1 image review](rig-independent.json): actual idle/fire/wrist/run views show long triangular arm-to-drape sheets. [R2 rest-space review](rig-r2-independent.json): severe strain exists before animation; no extra render requested. |
| WebP static reuse adapter | Accepted for its narrow offline contract | [Twelve independent adverse cases](adapter-adversarial-r1.json) pass. [Raw actual-pair comparison](reuse-raw-independent.json) preserves all oriented attribute triangles and image bytes; standard PBR/sampler defaults normalize. No measured graphics-speed improvement. |
| One wind-court pilot | Accepted for bounded art and integration | [818-ray fixture](world-adversarial-r3.json), [all sixteen matched actual images](world-visual-r4.json), and [fourteen canonical integration checks](world-integrated-r4.json) pass. The latter clones the actual 0.65 m player capsule and detects a deliberately reintroduced obsolete AABB. |
| Optional CC0 stone finish | Accepted as a material-direction study | [Six actual paired originals](world-pbr-study.json) improve stone depth/readability; source kit and CC0 map hashes verified. No runtime material promotion or hardware cost qualification. |
| Reused diya and cast presentation | Accepted as an isolated visible presentation study; strict AABB gate remains failed | [Final source identities](vfx-source-identity.json), [twelve lifecycle counterexamples](vfx-adversarial-r1.json), [corrected actual images](vfx-visual-r2.json), and [exact geometry diagnosis](vfx-exact-geometry-review.json). No gameplay integration or hero-animation acceptance. |
| Physical GPU, online match, whole-game quality | Unrun | Software data checks and isolated captures cannot establish these claims. |

The [acceptance contract](acceptance-contract.json) freezes the source and
counterexamples. Existing C1–C8 rejected hair mechanisms are not reclassified
as accepted. Visible pits in the generated source are not evidence of open
boundary holes: the raw exact-coordinate audit and Blender's topology-changing
`remove_doubles` diagnostic measure different things. The latter removed 454
faces and created diagnostic boundaries; it does not describe source holes.

The cleanup independently preserves every non-position/normal byte and every
coincident seam group. Only 785 vertices move, at most 0.00129661 source units
for a 1.00213-unit source height. This supports safe source isolation; it does
not turn an imperceptible cleanup into accepted sculpture. Its canonical
original, failed candidate and five originals are retained by the cleanup owner.

For the initial rig, an independent arithmetic check agrees with the owner's
48 localized worst edges. The evidence supports anatomical donor leakage:
adjacent wrist vertices receive arm and leg influences, then separate by about
0.8 m under a pose. This is distinct from UV seam splitting. Full-model skin
evaluation and native reimport are not claimed by that arithmetic check.

The one corrected transfer reduces some maxima but introduces rest-space
strain: an original 3.65 cm edge becomes 35.7 cm during arm repose. Twelve
worst-edge coordinate calculations independently agree with the report; 846
rest edges change by more than 2 cm. The corrected pose's new rest state cannot
replace the original source-fit denominator to conceal that damage. It fails
eligibility before another expensive render or runtime export.

For both adapter outputs, raw materials/textures/samplers are **not** JSON
identical. Explicit default PBR values are omitted and an implicit default
repeat sampler becomes explicit. The independent report records the exact
observed differences and resolves only those standard defaults. Geometry and
embedded WebP payloads are exact. Rama saves 292 bytes and the diya 336 bytes;
triangle/vertex counts are unchanged. These are compatibility results.

Run the independent probes from the repository root:

```sh
python games/yuga-native/docs/research/ten-rounds-oct23/review/source_glb_audit.py

python games/yuga-native/docs/research/ten-rounds-oct23/review/raw_pair_review.py \
  --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb \
  --candidate /workspace/scratch/ten-rounds-oct23/reuse/rama-freeze/candidate.glb \
  --report /absolute/writable/raw-rama-review.json

YUGA_REUSE_DEPENDENCIES=/workspace/scratch/production-reuse-oct23/reuse-art-tool \
  node games/yuga-native/docs/research/ten-rounds-oct23/review/adapter-adversarial.mjs \
  /absolute/writable/adapter-review.json

/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 --headless \
  --path games/yuga-native \
  --script res://docs/research/ten-rounds-oct23/review/world-adversarial.gd \
  -- --report=/absolute/writable/world-review.json

/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 --headless \
  --path games/yuga-native \
  --script res://docs/research/ten-rounds-oct23/review/world-integrated-adversarial.gd \
  -- --report=/absolute/writable/world-integrated-review.json

/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 --headless \
  --path /workspace/scratch/ten-rounds-oct23/vfx/project-05 \
  --script /workspace/ANDOLAN/games/yuga-native/docs/research/ten-rounds-oct23/review/vfx-adversarial.gd \
  -- --report=/absolute/writable/vfx-review.json
```

The official headless engine used here is Godot 4.6.3,
SHA-256 `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`.
These commands do not invoke the shared graphical render lane. Local dependency
and stage paths are prepared by their owners and are not portable installation
claims. The source audit is intentionally pinned to this source and workspace.

Meaningful first observations are retained. [World probe R1](world-adversarial-r1.json)
initially failed on automatic duplicate-node name suffixes and one ray placed
exactly on a capital edge; [R2](world-adversarial-r2.json) excludes generated names
from geometry identity and samples the face interior. No worker geometry or
collider assertion was relaxed. The [initial raw adapter comparison](reuse-raw-independent-r1.json)
retains the raw metadata inequality, and the final report separates it from
resolved semantic equality. [Project-03 VFX audit](vfx-source-identity-project03.json)
records a superseded stage that was internally exact while three authoring files
continued changing. [Project-05](vfx-source-identity-project05.json) binds the first
actual VFX run; the final project-07 audit binds the corrected presentation.

The first integrated reviewer probe did not parse; the next passed with a
surrogate 0.35 m capsule but incorrectly named it the real player size. Both
observations are retained with [explicit corrections](world-integrated-probe-corrections.json).
The final fourteen-case probe clones the actual 0.65 m world-player capsule,
preserves the eight-body array order, checks the roof and recessed facade, and
detects the reintroduced obsolete full box before confirming restoration.

For VFX, the initial actual cast view clipped windup strokes and lost day caption
contrast. One corrected capture fixes those visible defects, but its conservative
enclosing-AABB fit still fails in eight contact frames. The failure and exit 5
remain recorded. Actual indexed geometry already fits the unchanged 575 px
margin (maximum bottom 545.91 px); floor clipping tightens it to 522.60 px.
Empty enclosing-box corners overestimate the geometry. This diagnoses the
strict failure; it does not rewrite it as a passing capture.

The matched world art run uses the original caller and a live isolated court
swap. The later canonical caller has separate headless integration evidence;
those art images are not presented as captures of the later source. Acceptance
of the isolated VFX study does not promote it into gameplay. No commercial game
client or assets were analyzed in this review.


Followup reviews retain their own exact source versions:

| Followup | Decision and evidence |
| --- | --- |
| Render-resource CI fixture | [Accepted test-only correction](render-resource-ci-review-final.json): strict metadata guards plus separate three-surface pilot resource checks pass 40/40. The unchanged legacy baseline still produces its same three expected failures. No product predicate was loosened. Remote CI remains the lead's responsibility. |
| Donor-groom omission mask | [Rejected](groom-mask-independent.json): three actual diagnostic views and decoded original-image witnesses show fragmented hair/cape boundaries. Full covered-texel followup finds 1,226 unsafe faces; the remaining 1,116 form 103 components. No deletion, fitting or export approval. |
| Reused courtyard element | [Accepted hardened known-source intake](map-intake-independent.json): fresh native 23/23 checks and unchanged independent 11/11 malformed-field counterexamples pass. Original failures and the earlier Compatibility/llvmpipe preview remain separately identified. No whole-map or visual-quality acceptance. |
| Next ten-round queue | [No critical planning contradiction found](next-ten-plan-review.json). This is a conditional execution plan; it grants no execution or completion credit. |

The [additive CI-step review](authoring-ci-workflow-review.json) confirms that
canonical assets are not regenerated, direct failures propagate and temporary
JSON evidence has explicit archive paths. This is a static workflow review,
not a remote CI success claim. The [curated groom checkpoint review](groom-checkpoint-scope-review.json)
verifies all 30 manifest/tool hashes and the saved master hash; it preserves
the rejected omission gate and distinguishes the owner's 18-check cold reopen
from independently replayed checks.
