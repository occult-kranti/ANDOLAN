# R2-10 independent motion/deformation review

**Verdict: corrected r6 passes this bounded source/CPU review; actual imported-candidate and continuous pixel acceptance remain pending.** The r5 candidate was rejected because four vertices in the required fixed 288-vertex ring moved, at most 9.876143661 micrometres. The corrected r6 holds the sampled original ring exactly. Neither result establishes finished character animation, full-game acceptance, hardware performance, or commercial visual parity.

Product: YUGA native. Branch: `game/yuga-native-production`. Source commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Runtime/assets/shared ledgers were not edited. Review ownership is confined to this directory and `/workspace/scratch/visual-round2/role-10`.

## Exact reviewed inputs

| Input | SHA-256 |
|---|---|
| Runtime baseline GLB | `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5` |
| Rejected r5 GLB | `2dbd60ae1ca090340a1b927f71f815da313e976d8645991ea3ecc73282f7dd88` |
| Corrected r6 GLB | `140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a` |
| Role05 actual runtime report | `8edd6d7dc9217d877a8a013f287b43a98d3a3869f5bb3cec387689df07e7a00d` |
| Role05 actual imported baseline mesh arrays | `1856cd1bb7046d2625862c7d60aa8916d5d17a5a889394cc9c722c4efa2fc7eb` |
| Original 288-vertex ring | `71cc40e8f5eb732382255cbb9ca2eca88f6306429c2c649f8223dbe5b4db0ccd` |
| Current independent reviewer | `daa8c4ca1998a4cfe634679a157e92bfb0f2f4d9be5159977d65be619408df6c` |

The obsolete `491c2c…` candidate is excluded. r5 repaired the earlier POSITION bounds but did not preserve the whole required ring; r6 repairs that separate defect. `review_deformation-r5-rejected.py` preserves the exact rejected-run script bytes (`b27eade8be0f51e3b039162b91f21b387a2162266fe4a300b00db5dc553a6f6c`). JSON reports pin full source and dependency paths.

## Executed checks and limits

- r5: 16/17 reviewer checks pass; exact fixed-ring gate fails. Rejected report is retained.
- r6: **17/17 reviewer checks pass**. All three edited primitive POSITION bounds match their actual arrays. All 288 original held positions have zero mapped rest displacement and zero displacement from all four facial targets.
- The reviewer uses an independent bone-by-bone skin evaluator, retaining actual quantized imported weights without renormalizing them. It agrees with role05's slot-by-slot evaluator to `6.661338147750939e-16` metres on the baseline face.
- The r6 source position deltas were mapped onto actual imported baseline vertices, then replayed through all **37 actual baseline runtime poses**. All 146 face/body attachment witnesses retain zero gap; 231 duplicate-inclusive lip vertex witnesses retain zero gap. Role05 counts 226 unique rounded lip/body locations, so these counts describe different witness enumeration.
- A separate barycentric ray implementation tested actual imported eye geometry at 63 frontal rays per eye for **13 independent left/right partial/full combinations**. Candidate and baseline visibility counts match at every combination. Full single-eye and combined closure cover every sampled eye ray.
- The baseline runtime report was reviewed, not rerun by this reviewer: 73/73 checks, including unique writer ownership, public blink/effort interpolation, finite 164-bone poses, aim extremes, five actual casts/releases, pause/reset/teleport, and cancellation. `baseline-source-integrity.json` independently verifies all seven current runtime source pins and the imported mesh dump hash.
- These are finite samples and frontal visibility checks. They do not prove every continuous pose, exhaustive triangle collision freedom, or fix the pre-existing rapid-reversal body issue. The candidate has not been imported by this reviewer; source-delta replay is explicitly distinguished from candidate-import evidence.

## Deliberately broken controls

| Mutation | Observed detection |
|---|---|
| Move one attachment by 1 mm | Gap becomes 0.999984751 mm, exceeding the 0.05 mm gate |
| Remove the left full-blink target | Left exposed-eye rays rise from 0 to 36; right stays 0 |
| Substitute full closure during half blink | Visible-eye rays change from 15 to 0 on each eye, detecting overclosure |
| Move sampled eye surfaces 20 mm forward | Both eyes expose all 63 rays during nominal full closure |

These controls were applied to in-memory copies only. The overclosure control checks a wrong partial expression, while the eye displacement control checks failed closure; neither is an exhaustive collision detector.

## Known baseline defect retained

The existing source face validator was freshly executed on r6 and returned **17/19**, exit 1. The two failures exactly match the baseline and r5: open central-cornea obstruction at left `[-0.004, 0.0018]` and right `[0.004, 0.0018]`, one sample among 25 per eye. These are pre-existing defects and remain open. Passing full-blink closure does not erase them.

## Exact commands

Run from `/workspace/ANDOLAN`. The first command intentionally exits 1 for the rejected fixed-ring candidate; the source-validator command intentionally exits 1 for the two known open-cornea failures. Only CPU work was run; no import or renderer was started.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/docs/evidence/visual-rounds/round2/role10/review_deformation.py --candidate /workspace/scratch/visual-round2/role-08/face-form-candidate-r5/candidate.glb --output /workspace/scratch/visual-round2/role-10/face-motion-counterexamples-r5-rejected.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/art/hero-rama-face/validate_face.py /workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb --report /workspace/scratch/visual-round2/role-10/candidate-r6-face-check.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/docs/evidence/visual-rounds/round2/role10/review_deformation.py --candidate /workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb --held-ring /workspace/scratch/visual-round2/role-08/face-form-candidate-r5/reconstruction.held-ring.json --candidate-face-report /workspace/scratch/visual-round2/role-10/candidate-r6-face-check.json --output /workspace/scratch/visual-round2/role-10/face-motion-counterexamples-r6.json
```

For exact rejected script provenance use the preserved `review_deformation-r5-rejected.py` snapshot; current script adds optional input paths without changing its numerical checks. Original stdout/stderr logs remain under the role10 scratch directory.

## Remaining acceptance gate and next owner

No raw continuous images were reviewed in this bounded pass: the 36-adjacent-frame baseline/candidate captures were not yet available. Do not label this an animated visual pass.

Role06 owns the serialized import/render lane. Role05 must replay the same attachment, held-ring, morph and actual-eye checks against r6's own imported arrays and record that exact asset hash. Then role10/root must inspect each of the 36 adjacent raw frames per source individually, with frame order and hashes, for seam cracks, lips detaching, partial/full lid intersection, surface popping and silhouette discontinuity. Match the recorded camera/pose/light controls; verify the actual blink closes and reopens, Kodanda releases, and Piercing cancels without releasing. Review the ordinary-speed sequence as a separate continuity check. The current 1.2-second capture contract does not include an independent-side blink/aim-extreme rendered matrix; that limitation must remain explicit.

Next owner: root schedules the candidate-import and pixel review when role06 completes. Any new candidate hash reopens this source gate. No runtime promotion is authorized by this report alone.
