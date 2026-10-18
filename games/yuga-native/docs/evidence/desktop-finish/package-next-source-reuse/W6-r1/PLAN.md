# Reuse the owned partial checkout for a later focus checkpoint

Plan only: no restoration, deletion, checkout or new package operation was performed. The current `f8dec5fa` package and its warm/cold qualification remain independent.

The existing checkout `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN` can be reused. Restore only the exact 2,732 historical art/evidence files removed under the [published recovery map](../../../../../../../docs/evidence/desktop-finish-package-source-cleanup-r1/recovery-map.json), SHA `fd3ad43d21c0bc118de05961edc438fbe4d75515c1cf6a18908571a4381a1f07`. Its [execution receipt](../../../../../../../docs/evidence/desktop-finish-package-source-cleanup-r1/execution-receipt.json) records the intentionally partial `f8dec5fa` checkout and 3,112,771,584 allocated bytes reclaimed.

Hard-linking canonical files into this checkout is unavailable: `/workspace/ANDOLAN` is device 27 and `/tmp` is device 34. Symlink substitution would change tracked file modes and fail existing provenance ancestry/symlink checks. Do not use Git ignore, skip-worktree or assume-unchanged flags to conceal the missing files.

## Bounded restoration procedure, after separate authorization

1. Wait for current package work and source checks to release the checkout; preserve every r1/r2/r3 output, current warm/cold capture, cache, import, Git object and generated UID file.
2. Recheck the recovery-map hash, expected detached HEAD and exact current deletions. Require every deleted path to belong to that map; reject unexpected tracked or untracked changes. Confirm the canonical Git object store remains available because the clone uses object alternates.
3. For every map row, verify the current checkpoint's tree still maps its path to the recorded Git blob/mode. Stream that exact blob into a temporary sibling; verify length and SHA-256, then restore only a missing destination as a regular file with its recorded executable mode. Reject symlink ancestors and existing changed destinations. Never overwrite a generated file.
4. Verify all restored hashes and Git modes; require a clean full tracked checkout. Recheck all 115 generated metadata files and the existing exact 113-entry non-runtime exclusion file unchanged. Record complete runtime/tracked/cache and preserved-output inventories.
5. Only then advance the same owned checkout to a separately reviewed and remotely verified focus successor. Audit its exact source delta and use a fresh output directory. Do not reuse or relabel current r3 manifests.

## Space reservation

The measured r3 build occupies 784,232,448 allocated bytes, so budget that observed footprint for a similar successor rather than assuming 650 MB. Restoration needs 3,112,771,584 bytes. A conservative pre-restoration gate is their sum plus 128 MiB for logs/metadata: **4,031,221,760 free bytes**, remeasured after current captures finish. This is a planning floor, not an assurance against unrelated concurrent writes.

The only proposed additional duplicate candidates are superseded r2 expanded payloads, subject to a separate exact ZIP byte/mode inventory, process/owner release and lead approval:

| Candidate | Observed allocated bytes |
| --- | ---: |
| r2 `build/yuga-native-linux-x86_64` | 209,657,856 |
| r2 `build/yuga-native-windows-x86_64` | 243,085,312 |
| r2 `extracted/yuga-native-linux-x86_64` | 209,657,856 |
| Potential total | 662,401,024 |

The retained r2 ZIPs are `88948751…306a0` (Linux) and `4c50c100…dfc7e` (Windows). The prior r2 qualification proves its original payloads; a fresh full comparison is required before any cleanup. The r1 export-only build has no expanded package directory. Nothing here authorizes removal of any ZIP, PCK, unique log, manifest, source receipt, r3 payload, or current warm/cold extraction. If the measured free space plus separately approved duplicates does not reach the gate, stop and report the exact shortfall; do not widen cleanup automatically.
