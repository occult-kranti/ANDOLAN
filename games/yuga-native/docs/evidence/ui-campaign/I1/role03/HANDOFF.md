# I1-03 resources and I3-06 package preparation

YUGA native, initially HEAD `00a204bfbf5e1de47a0a12a233841d7f3a2475ab` plus the explicitly pinned U5 freezes; finalized support and runtime are committed at `4bd82ad5909ce949df536b2809d8b37a7f9d20f8`. This assignment checks combined runtime resource ancestry and prepares the portable package. Actual export/archive execution is a subsequent distinct I3-06 assignment under `../../I3/role06`; this I1 preparation does not change the current `yuga-rama-hero-2026-10-17` release.

## Executed evidence

- `resource-preflight-r2.json`: 712/712 checks on U5 r1; manifest `720d124a51d3c31b95424889a1047360720c078cda1480405f4e705442cd5ecb`.
- `resource-preflight-r3-u5-final.json`: 712/712 on U5 r2; manifest `0f4871dd0b09cca7f240454f33016bbe154567f0840fc15d6e7f164c3871666f`. This derivative contains 750 source files and 350 imported/cache files. It remains a U5 freeze, before the final I1 overview correction.
- `resource-final-I1.json`: 712/712 on final I1, manifest `9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088`, with 755 frozen source files and 350 imported/cache files. The subsequent I3 preflight binds 518 actual package runtime files to this freeze and 601 runtime/ancestry/font/notice/support files to Git commit `4bd82ad`.
- Both audits independently reconcile all 173 import descriptors: raw source, destination set, actual raw MD5, ordered imported payload MD5, and SHA-256 records. The four accepted R7 groom/cloth payloads match their actual R3 capture import receipt. Canonical schema-4 validation checks 66 authoring sources, then binds the frozen runtime subset and exact NOTICE. Three fonts and five font notice files retain their pins.
- `package-provenance-cases-r2.json`: 286/286 source/fixture assertions on finalized support. The two actual FontFile engine checks from the earlier 288-check R3 run were **not rerun** here. The earlier 286-check receipt remains separately retained.
- `first-load-package-cases-r2.json`: 108/108 PCK assertions, including first-load resource/remap and canonical-path adversaries. The earlier 99-check receipt remains retained.
- `package-preparation.json`: 9/9 preparation checks. Linux and Windows engine hashes, platform launch text and all 24 copied notices verified. The generated captions now match the actual **Watch duel** button. Linux dynamic dependencies were read from the engine ELF; no engine was executed.

The audit's first attempt applied the complete authoring validator to a runtime-only capture freeze. It correctly failed on absent historical authoring inputs. `resource-preflight-r1-failure.json` retains that boundary error; the corrected audit validates complete ancestry in the canonical checkout and explicitly binds only the runtime subset to the freeze.

## Concrete package correction

The earlier inspector accepted a structural fixture without boot, loader, or launch files. The exact accepted fixture and old validator identity remain in `missing-first-load-accepted-before-fix.pck` and `first-load-package-counterexample.json`. This fixture was never executed.

`tools/package-native.py` now requires exact boot scene, boot script, scene transition, launch shell and shared theme resources. Each must be either a direct resource or one strict Godot remap with its exact compiled destination. Missing targets, ambiguous bindings, wrong sections, defaults, duplicate keys, traversal, cycles and script/scene substitutions are rejected. Actual historical Godot 4.6.3 PCK descriptors were inspected read-only to establish the compiled layout; that observation is not new-package acceptance. `tests/traversal_security_cases.py` owns the new adversaries. The existing font and hero ancestry contracts remain intact.

Independent review found another concrete structural gap: dot segments and repeated slashes could bypass raw-name duplicate checks. Final support rejects noncanonical spelling and tracks duplicate relative identity, including mixed bare/`res://` names. The independent original accepted PCKs remain under `../role01/first-load-review`. Its final **22/22** receipt SHA is `0ad3cfa88658ac7328361eb22f83bb462ba662bc12a99ff746ec556817b8d6b0`. No fixture pack was executed and actual Godot shadowing is not claimed. No runtime or asset files were modified by this assignment.

## First-load boundary

The static immediate boot closure has seven files: boot scene/script, scene transition, shared theme and three fonts. Hero GLBs are outside that immediate closure. Scene route closures for courtyard, Confluence and the film were resolved. Source/cache consistency does not prove startup timing, decoding, scene progress or lifecycle behavior. UI03 owns actual integrated execution, and I2 owns the subsequent repeated-resource/loader checks.

## Reproduction

Run from `games/yuga-native` with CPU affinity 2,3 and one BLAS/OMP thread:

```sh
taskset -c 2,3 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python docs/evidence/ui-campaign/I1/role03/audit_resources.py --project . --freeze /tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native --output /tmp/i1-resource-recheck.json
taskset -c 2,3 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tests/traversal_security_cases.py --report /tmp/i1-pck-recheck.json
taskset -c 2,3 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tests/rama_package_cases.py --groom-review /workspace/scratch/visual-round3/role-14/r7-review-r2 --report /tmp/i1-provenance-recheck.json
```

The accepted R7 review directory remains required by the provenance adversaries. Old duplicate proposal projects are unnecessary.

## Package handoff and remaining gates

Final I1 runtime/freeze reconciliation is complete. Root owns any successor source disposition. Package from the complete committed checkout; the capture freezes intentionally omit authoring history and package tools. `PACKAGE-COMMANDS.md` records the serialized export/archive and exact Linux execution procedure. Windows remains archive-validated and unexecuted until separately run.

No import, export, full archive build, packaged execution, new visuals, publication or current-release update occurred here. Existing historical release workflows do not automatically qualify a new Rama/UI tag. Final action/capture and release dispositions remain with their owners.
