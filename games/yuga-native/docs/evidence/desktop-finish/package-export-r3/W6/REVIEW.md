# Explicit public-runtime package, source f8dec5fa

Export and archive qualification passed on exact committed source `f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1`. Actual extracted-package execution is pending W1. This packet does not turn the previous official-runtime shader wait into a successful run.

The official Linux engine `f64d4ed1…bfeb3` performed PCK export and both imported-font proofs. The Linux ZIP explicitly bundles the reviewed unmodified public-source `template_debug` runtime `dce0422d…730f`, with its original build/source records and MIT/COPYRIGHT references. Its START-HERE and PACKAGE-MANIFEST distinguish exporter from runtime. The Windows executable remains `ef90e929…4cb00` and is unexecuted.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Linux ZIP | 97,821,471 | `913e2b82b9a71977bf361349e225ae0295a9dd08f1e0a0a68d7b3b7d3df4426c` |
| Windows ZIP | 146,132,379 | `ee8026ca24b47a4f43b875a8aeea39aa680fb3161eaad4327f970a404ccad722` |
| Each PCK | 70,128,028 | `f55b5417e38b6a5b46ff2b12ec22890509287f84ad1fe2fb62c87190c76a7197` |
| Export manifest | 452,532 | `c472ef5278b4c35b8226d654bbaf5c0061b98c00a4be20c7a3a1dbe8600adb54` |
| Package manifest | 10,563 | `6df86cc23505cbe6fc1a22d00e86cb9afc03c7733b69e0b068c40889d9c0ff36` |

The two PCKs contain 543 entries and remain byte-identical to r2. All 39 Linux and 34 Windows ZIP members passed CRC and byte-hash verification. The copied Linux executable matches the selected dce identity; the Linux-specific provenance files are present, and Windows contains no public-runtime descriptor. The existing font and native-contract gates pass at both export and package phases. No engine warnings or errors were found in the complete logs.

The owned full checkout was advanced from `5542e616` to the exact successor without creating another clone. All 16,982 tracked files and 552 runtime files matched their pre-export hashes afterward; Git status was clean. The 115 previously generated UID files and approved 113 exact non-runtime exclusion entries were preserved. Both r1 and r2 build/log outputs were rehashed unchanged. Only the editor filesystem cache index changed; imported resource payloads did not. See [qualification-receipt.json](qualification-receipt.json), [preparation-receipt.json](preparation-receipt.json), and [cache delta](cache-after-delta.json).

Export completed in 13.265 seconds; packaging in 21.586 seconds. The first read-only reviewer assumed a nonexistent `git.dirty` field and raised a KeyError after successful export. Its [failure record](export-review-r1-failure.json) is retained; the corrected review checks the actual `native_worktree_status` field and full before/after source hashes. The package process independently repeated its source and identity guards.

Raw archives and expanded packages remain at `/tmp/yuga-desktop-integrated-package-r3/build`. [SHA256SUMS.txt](build-records/SHA256SUMS.txt) covers the two ZIPs and two manifests. This durable packet keeps exact small receipts, complete logs, commands, source inventories and the packaged runtime wording without duplicating the large archives. The tracked-source inventory is losslessly compressed with raw and stored hashes.

No owned engine remains. W1 received the exact artifact hashes and explicit renderer-lane release. Only the separately approved historical art/evidence duplicate cleanup in the owned checkout was released; runtime files, configuration, imports, Git metadata, UID metadata and all attempt/output roots remain protected. Actual warm and cold execution, Windows execution, listening quality and physical-GPU performance remain separate gates.
