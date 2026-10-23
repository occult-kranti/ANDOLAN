# Generated Rama: bounded cleanup, rejected

The actual same-topology candidate **fails the artistic gate**. All three reviewers inspected the locked source/candidate frames and agree: front/costume remain stable, but rear hair remains pitted and fragmented, with an uncontrolled transition into the cape. The original remains the rig baseline. No runtime asset, LOD or canonical hero was changed.

| Step | Executed result |
| --- | --- |
| R1 source audit | 93,214 imported vertices / 96,660 triangles. Exact-coordinate union retaining every face: 45,565 positions, 20 components, **zero boundary edges**, 1,570 edges with incidence above two. |
| R2 cleanup contract | [Spatial/texture mask, protected regions and delta budgets](contract.json), based on actual front/rear defects. No general hole fill or whole-body remesh. |
| R3 bounded derivative | 785 vertex positions moved; max displacement 0.001296605 source units; only 10,564 POSITION/NORMAL bytes changed. UV, images, indices, materials and all other bytes remain exact. |
| R4 locked comparison | Five fresh 640×800 Blender frames completed, exit 0: [front source](comparison/front-original.png), [front candidate](comparison/front-candidate.png), [rear source](comparison/rear-original.png), [rear candidate](comparison/rear-candidate.png), [changed-vertex diagnostic](comparison/rear-diagnostic-mask.png). **Rejected.** |
| R5 promotion / LOD | Not run: the artistic gate failed. No production credit. |

[Rejection](rejection.json) records the decision by cleanup, independent quality and root review. [Comparison receipt](comparison/comparison.json) pins every frame. [Frozen studio](comparison/studio-contract.json) records camera, light transforms/energies, floor, color management and source geometry digests. The diagnostic red mask is not a candidate material or final look.

The first Blender weld diagnostic reported 618 boundary edges because `remove_doubles(dist=1e-7)` also removed 454 duplicate faces. Those are **not source holes**. [The corrected audit](reports/source-audit.json) separately retains every original face and agrees with independent raw-GLB analysis. Raw imported seam splits also inflate component/boundary counts. Tiny islands cross hair, ornaments and clothing, so none were blindly deleted.

The candidate groups positions with a rounded `1e-7` coordinate key; its 45,565 groups match the independently exact-coordinate union for this source. Three masked Taubin pairs and a 0.0025 displacement cap reduce a local residual by about 8.6%. That measures smoothing, not silhouette, anatomy, coherent lock flow or game quality. The selected mask excludes upper pits; its safe, small perturbation does not repair the overall form.

[Independent byte verification](reports/verified-patch.json) passed. [Nine real-candidate counterexamples](reports/counterexamples.json) passed: unchanged source, truncation, image or UV mutation, protected-region movement, excessive movement, nonunit normals and nonfinite positions are rejected. These are mechanical eligibility tests, not art acceptance.

## Reproduce without replacing runtime

Run from `/workspace/ANDOLAN` with Blender 4.3.2. Use a fresh output directory each time. Audit/candidate operations use one CPU thread; coordinate the shared heavy lane before the two-thread render. Source SHA-256 is `0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b`.

```sh
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-source-cleanup/audit_source.py -- --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --output /workspace/scratch/cleanup-audit-new
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-source-cleanup/cleanup_candidate.py -- --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --output /workspace/scratch/cleanup-candidate-new
python3 games/yuga-native/tools/hero-source-cleanup/verify_patch.py --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --candidate /workspace/scratch/cleanup-candidate-new/rama-hair-micro-cleanup.glb --report /workspace/scratch/cleanup-candidate-new/verified.json
python3 games/yuga-native/tools/hero-source-cleanup/test_verify_patch.py --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --candidate /workspace/scratch/cleanup-candidate-new/rama-hair-micro-cleanup.glb --report /workspace/scratch/cleanup-candidate-new/counterexamples.json
blender -b -t 2 --python-exit-code 1 --python games/yuga-native/tools/hero-source-cleanup/render_comparison.py -- --studio /workspace/scratch/production-stage-oct23/art/generated-intake-r1/rama-generated-source-intake.blend --candidate /workspace/scratch/cleanup-candidate-new/rama-hair-micro-cleanup.glb --candidate-report /workspace/scratch/cleanup-candidate-new/candidate.json --output /workspace/scratch/cleanup-comparison-new
```

The experiment GLB remains in scratch (exact location/hash in rejection.json); no rejected 4.48 MB duplicate is added to the repository. Original source, packed-studio recipe and five new unique comparison originals are retained. Do not delete the pinned studio while another owner needs it.

The next useful task is the [specific donor/retopology contract](NEXT_RETOPOLOGY_CONTRACT.md), using existing project-owned sources rather than another smoothing pass. It remains a proposal requiring saved artist landmark/mask decisions and four-view clay acceptance.
