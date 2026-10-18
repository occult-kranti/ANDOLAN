# I3-06: portable package provenance and build

Final candidate **package-r3** is built from committed source `9e81a7c849837dea477ddb5a8c93f43665774573`. Both archives pass structural verification. Actual Linux input and pixels belong to UI03 and the independent I3 reviewers; Windows remains unexecuted. No publication occurred.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Linux ZIP | 137812335 | `56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5` |
| Windows ZIP | 145813678 | `16f6e210fef90f26c1c725e503805fb5e9c4ee76d64e86cb2ff7b0788ea186c5` |
| Each platform's PCK | 69804988 | `d387d34ad37fc959f974b9ced0107d5ad2a0e2505e55a090dd20fc583d62aa27` |
| Export manifest | 397267 | `9b181f1c67e32de6481cd9256c61b38eb54de6ce2afe54e05f2a68ae2931d75b` |
| Package manifest | 12765 | `12010a4eae0b6645d946e5aaa8b52daba5f8f233425356aa942891ab0b87c1b2` |

Original artifacts are in `/workspace/scratch/ui-campaign/I3/package-r3`. Small manifests and execution logs are copied under `package-r3/` here. `BUILD-RECEIPT.json` pins the build, source closure and validation scope. Each ZIP has 29 entries; each PCK has 519. The runtime signature is `61700ca7e3a77e20ae81175ad5babd337d7094ab82907801ac2b20ee85bce5e4` across 525 runtime/config/import-descriptor files.

## Executed checks and corrections

The initial complete preflight verified 518 runtime files against final I1 freeze `9919dccb…` and 601 runtime/ancestry/font/notice/support inputs against committed Git blobs. The first export generated seven absent UID sidecars, so the unchanged-source guard rejected it before packaging. Root committed those exact additions at `83f88f84`; `uid-overlay.json` records all seven and every preexisting runtime file's equality. The R1 filesystem scan also automatically reimported the woven roughness texture. All 350 existing imported/cache files remained byte-identical; the log and explicit reconciliation are retained. No GLB import occurred.

R2's archives passed structural checks but were rejected after CI found that native contract revision 5 still pinned the previous player source. `rejected-package-r2/REJECTION.json` independently reconstructs the exact committed mismatch: expected player `d02f1312…`, actual `54beb1c8…`. Its original archives, PCKs and manifests remain historical. Root may remove only hash-verified expanded staging duplicates; unique archives and evidence remain.

The correction intentionally advances native content to revision 6 while preserving the prior catalog/descriptor fixtures and browser/production profiles. Only the runtime catalog and `native_contracts.gd` change from the UID-only source; the other 523 runtime files are exact. `content6-preflight.json` binds these two changes and all 32 contract inputs to final Git blobs.

The permanent package preflight now executes the actual contract checker before either export or package engine calls. It requires successful nonempty checks, all required content-source checks, exact report source hashes and stable catalog/tool/source/fixture bytes. Export and package proofs must match, and inputs are checked again before either artifact is accepted. Both actual final phases pass **51/51** source assertions, bound to **32 files**.

Focused tests pass **13/13**, including the real historical mismatch, a newly changed player, rejection before engine access in both entry points, replayed/empty proofs and retained-input changes. Independent review passes **7/7**, including mutation after checker execution, omitted source binding and duplicate checks. The support SHA is `3152a52cc491a4b5037defa47106f5b4f7b153d40383d963b99049964b4bfb26`; no font/hero/PCK acceptance rule was relaxed. The focused historical reconstruction test uses the retained `83f88f84` Git object; shallow clones need that object to rerun that historical case. The package gate itself requires no Git history.

## Final archive validation

- Full ZIP member sets, CRCs and every payload SHA pass for both platforms. Official engine byte identities and Linux executable modes match. Launchers point to the adjacent PCK, and instructions use the actual **Watch duel** caption.
- All 24 notices copy exactly, including the five font license/source notices. The 66-source hero ancestry remains exact.
- Same-export actual FontFile data matches the three pinned raw fonts. Exact font descriptors and imported payloads qualify in both PCKs without assuming permanent hashes for generated import caches.
- All five boot/loader/launch/theme mappings resolve to their exact compiled destinations. Canonical pack paths and all payload integrity fields pass.
- Export and package sources remain unchanged. R3 logs are clean, with no asset import/reimport. The phase ran on CPU 0,1 with one BLAS/OMP thread and isolated XDG state; that lane is released.

Independent I3-02 archive review passes 10/10, with a separate 4/4 check binding all 525 source blobs to Git. Its own initial probe-schema fixture error remains retained and did not identify a package defect. The exact Linux archive and source manifest were handed to UI03 for a single fresh extraction and actual input/capture.

This role does not claim portable gameplay or visual acceptance. The official full-engine package is larger than a release-template package. Linux execution/capture and final integration disposition remain separate gates; Windows and publication remain unexecuted.
