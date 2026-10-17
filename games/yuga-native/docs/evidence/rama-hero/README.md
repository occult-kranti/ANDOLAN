# Rama evidence: start here

This archive supports one offline Rama hero preview, not completion of the full game or commercial-game visual parity. The editable character and continuous clips are real 3D assets. The supplied concept painting remains a separate art target; hair, cloth, facial expression and production material/LOD work remain limited.

## Current source

The accepted expiry correction has 352 runtime files and aggregate SHA-256 `65b5b8f4baff7bf5393b2051b96181bfed6fc48436869428835177e3a05566e3`. The new hero GLB is `667f3a215a7b868e3bdbcde880a73d42b68b29af1303db4e1d99b93f73cf2b50`. The replacement portable package was exported from clean commit `9eb6323ef20d8f10436a893ffcd434096686247a`; its full five-ability recording passes owner and independent QA review.

[Current package manifests](package/) verify all 352 runtime sources against the release commit and all 350 PCK resources. [Package R2](package-r2-expiry-finding/) preserves the prior clean export, superseded by the Guardian boundary/HUD timing finding. Its actual Settings reviews remain valid for unchanged screen sources. Export validation does not establish execution; Windows remains unexecuted. Exact actual-input review belongs to [window/](window/), and current release/public verification is recorded separately when completed.

## Read by question

| Question | Evidence |
| --- | --- |
| Is the character editable and attributable? | [Art provenance](../../../NOTICE/RAMA-HERO-PROVENANCE.json), [independent R7 byte audit](qa/r7-independent-byte-audit.json), [GLTF validator](source/gltf-final-r7.json). Two preserved non-root skinned-mesh hierarchy warnings are assessed in actual Godot deformation review. |
| What does the animation actually look like? | [Full motion reel](motion/rama-motion.mp4), [side/stop reel](motion/side/rama-motion.mp4), [motion review](motion/REVIEW.md), [independent QA](qa/review.json). Encoded frame rate is sampled simulation, not real-time GPU performance. |
| What do all five abilities look like in the world? | [Final gameplay reel](gameplay/rama-five-abilities.mp4), [owner review](gameplay/REVIEW.md), [independent R3 review](qa/final-review/gameplay-r3-review.json); 363 frames and 25 stills with state/source checks. |
| Do actions affect real receivers consistently? | [Strengthened 138 actual-world integration checks](qa/final-review/expiry-regression/summary.json), [85 focused combat checks](combat-expiry/r2-boundary/rama-ability-owner-r20-authority-boundary.json), [expiry defects and fixes](combat-expiry/). The latest normal-update regression and independently accepted Guardian probe address the R2 timing defect; older reports preserve their original inputs. |
| Are source contracts and package contents validated? | [Boundary/HUD contract, pin and package checks](contracts/boundary-hud-fix/), [current clean export](package/), [package fixture repair](ci-package-fixture/). |
| Are screens tested with actual input? | [Window review](window/REVIEW.md), separate from [headless UI checks](ui/) and the [Settings regression](window/settings-entry-fix/). |
| Were failures retained? | R6 drape and R1 Guardian frames in [QA](qa/review.json); clock/fade regressions in [combat-expiry](combat-expiry/); initial Settings captures in [window](window/); original CI failures in [ci-first-candidate](ci-first-candidate/), [ci-package-fixture](ci-package-fixture/) and [ci-relay-fixture](ci-relay-fixture/). |

`source/` preserves the first candidate. `source/final/` means the post-expiry, pre-Settings-fix snapshot; it is not relabelled as the later export. `package-r1-settings-finding/` preserves the superseded package and clean source identity. Each report keeps its original inputs and scope. The rejected R2 boundary capture is retained under `combat-expiry/r2-boundary/`; the accepted focused correction is under `combat-expiry/guardian-probe/`. Use `package/` for the current portable payload and its explicit execution boundary.

`archive-manifest.json` hashes committed archive members; run `python3 games/yuga-native/tools/check-evidence.py --git-ref HEAD` from the repository root. Report integrity cannot turn an unrun or limited quality gate into a pass.

The final full gameplay capture, new-package Linux smoke and [full CI on `9eb6323`](ci-final/review.json) have passed within their recorded scope. [Public artifact verification](published/REVIEW.md) confirms all seven downloaded assets, complete ZIP payloads and both videos. See [independent acceptance](../../RAMA_HERO_ACCEPTANCE.md) for the authoritative disposition.
