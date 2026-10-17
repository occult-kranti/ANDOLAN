# R2-13 resource / LOD review

Corrected r6 source census and bounded imported lifecycle checks pass.
Product: YUGA native. Source commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
The candidate measured here is corrected role08 **r6**, SHA-256
`140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a`.
The old r5 scratch project and r2 LOD overlay are excluded as candidate evidence.

| Source asset | File bytes | Vertices | Triangles | Materials | Texture entries | Embedded image bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_near | 34,322,216 | 234,846 | 408,316 | 13 | 17 | 10,138,144 |
| baseline_mid | 25,049,516 | 126,565 | 216,544 | 13 | 17 | 10,138,144 |
| baseline_far | 20,507,548 | 82,869 | 140,966 | 13 | 17 | 10,138,144 |
| candidate_near | 34,322,216 | 234,846 | 408,316 | 13 | 17 | 10,138,144 |

Independent binary/accessor census confirms **zero resource-cost delta for near, mid and far**.
Candidate mid retains 126,565 vertices / 216,544 triangles / 25,049,516 file bytes;
candidate far retains 82,869 vertices / 140,966 triangles / 20,507,548 file bytes.
Both retain 13 materials and 17 texture entries. The same image and identity
comparisons pass for each matching baseline/candidate LOD. Role14 confirmed
`form-lods-r3` frozen with the exact hashes recorded in the census.
Near retains 18 primitives, one source skin with 164 unique joints, nine embedded
animations and eight morph accessors. Morph accessors expand to 534,144 logical
bytes; their distinct stored buffer views occupy 218,428 bytes. Skin attributes
occupy 4,696,920 logical bytes plus 10,496 inverse-bind bytes. Skin, topology-index,
morph and embedded-image bytes match the baseline; material/texture declarations,
node/skin structures and animation declarations also match. This verifies cost
and these identities, not deformation or final art acceptance. The full source
metrics and image hashes/dimensions are in `face-resource-census.json`.

Vertices are summed over mesh primitives; image bytes are encoded payload size.
These are not resident GPU memory measurements. GLB files each embed the same
10,138,144 image bytes; adding those file sizes is not the runtime texture cost.
The runtime LOD binder loads candidate scenes without cache ownership, clones only
body/bow meshes, remaps their material slots to near resources and frees temporary
candidate scenes. It excludes each candidate face and keeps the original face.
Code requires one matching 164-bone skeleton and creates four extra mesh instances
and two named skins for two LODs. This source-inspected behavior is now confirmed by the bounded actual r6 lifecycle check below. Source hashes are in `source-pins.json`.

The facial component claims a unique morph mesh using ownership metadata and
rejects a second writer. Materials/finish components use per-owner resources and
restore exact prior overrides. Existing tests cover those contracts, but synthetic
fixtures cannot establish candidate import identity or candidate runtime behavior.
The stock facial suite's `--asset` path invokes GLTFDocument's runtime importer;
this review will instead use the already imported PackedScene for actual checks,
in keeping with the serialized import ownership assigned to role06.

The form candidate does not include the separate roughness-mip or SSS diagnostics;
their texture/import settings must not be silently counted as part of r6.
No consumer-GPU FPS, physical GPU frame time, universal leak freedom, screenshot
acceptance or release approval is claimed.

Executed command (CPU0,1):

```sh
taskset -c 0,1 python3 games/yuga-native/docs/evidence/visual-rounds/round2/role13/census.py --baseline games/yuga-native/assets/heroes --near /workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb --output games/yuga-native/docs/evidence/visual-rounds/round2/role13/face-resource-census.json
```

Final source command adds `--lod-directory /workspace/scratch/visual-round2/role-14/form-lods-r3/overlay/assets/heroes`.
Result: exit 0, six sources measured; all 18 cost deltas zero and all eight
listed identity comparisons true for each near/mid/far pair.

Role06 completed the serialized corrected import into
`/workspace/scratch/visual-round2/capture-forms-project-r2`; its receipt is copied
as `candidate-import-receipt.json`. Role13 independently hashes all three files
in that project and confirms they equal the frozen r6 source and receipt pins:

- near: `140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a`
- mid: `44bf3961fa52aef0b1a212dff05dcc6bda5c3cae7c9eaf00303aba9f39d45416`
- far: `62e65520da49d4f81d8cf0755f77df214f7ce0929d4818c13f62555b300a8f43`

Role13 executed the corrected actual PackedScene lifecycle probe on CPUs 0,1:
**81/81 checks pass, exit 0, no engine errors or leak-warning lines.** Four complete
load/near-mid-far-mid-near/reset/release cycles retained one 164-bone rig, one
facial writer, four body/bow LOD clones and two named skins. The second facial
writer was rejected. Each cycle retained 22 calibration materials, 24 standard
finish materials and 15 secondary finish bindings; repeated configuration kept
resource identities stable. Face/LOD updates preserved all bone poses. Another
hero sharing the imported source retained its exact materials. Release restored
original material identities, and weak references confirmed release of retained
owned clones, their mesh resources and calibration materials.

The original midpoint expectation was a **diagnostic fixture defect**: at 75° FOV,
720px viewport height and measured 2.079514m hero extent, 8m projects 121.953px and
correctly selects far. The corrected 4m midpoint projects 243.907px, within the
184–357px band that selects mid from either direction. The original 69/77 result,
all eight failed midpoint assertions, log and exact script are preserved in
`failed-8m-fixture/`. The corrected probe retains every ownership/cost assertion
and adds four explicit measured-projection assertions. `imported-lifecycle.json`,
`imported-lifecycle.log` and `lifecycle-execution.json` preserve the passing run,
source hashes and exact command/environment. Imported scripts and asset hashes
were rechecked against the original reviewed pins and remain exact.

Role13 also independently inspected role06's eight existing suite reports/logs:
facial 38, LOD binding 38, selector 27, materials 38, finish 53, adversarial finish 7,
abilities 85 and hero integration 138 — **424/424 checks, all exit 0, clean logs**.
Role06's facial run omitted `--asset` and therefore covers its synthetic fixtures;
the separate actual PackedScene probe above establishes bounded candidate
lifecycle behavior. These eight suites were executed by role06, not role13.
Their exact commands/report/log hashes are in `lifecycle-execution.json`.

No runtime assets, shared project, engine cache or stock tests were edited by
role13. No imports or renders were performed by role13, and no actual frames
were visually reviewed. Four clean cycles are bounded evidence, not proof of
universal leak freedom. Physical GPU frame time/FPS and rendered LOD/art
acceptance remain open. Next owner: root/art review for visual acceptance and
later hardware performance testing.
