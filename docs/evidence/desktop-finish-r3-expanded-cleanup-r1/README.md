# Separate r3 expansion and Windows-PCK recovery plan

**Prepared and verified only; zero files deleted.** This separate map leaves the sealed r2 102-file map unchanged. Root must push this map/guard and independently authorize execution. W1 and W6 released the exact paths below after both e69 diagnostic takes were sealed; R6 uses separate children. Their releases are recorded in [ownership.json](ownership.json).

| Exact target | Files | Allocated bytes |
| --- | ---: | ---: |
| `/tmp/yuga-desktop-integrated-package-r3/build/yuga-native-linux-x86_64` — expanded files only | 39 | 156,274,688 |
| `/tmp/yuga-desktop-integrated-package-r3/build/yuga-native-windows-x86_64` — expanded files only | 34 | 243,085,312 |
| `/tmp/yuga-desktop-integrated-package-r3/extracted/yuga-native-linux-x86_64` — expanded files only | 39 | 156,274,688 |
| `/tmp/yuga-desktop-integrated-package-r2/build/yuga-native-windows.pck` — this standalone file only | 1 | 70,131,712 |
| `/tmp/yuga-desktop-integrated-package-r3/build/yuga-native-windows.pck` — this standalone file only | 1 | 70,131,712 |
| Total | **114** | **695,898,112** |

The logical total is 695,603,096 bytes. Every file's full length and SHA-256 matches its exact retained ZIP member. The r3 Linux ZIP is `913e2b82…4426c`; r3 Windows is `ee8026ca…d722`; r2 Windows is `4c50c100…dfc7e`. [Per-archive provenance](archive-provenance.json) distinguishes r3 source `f8dec5fa` from the older r2 Windows source `5542e616`. The map's latest-source ancestry gate is f8; it does not relabel the r2 PCK as an f8 build.

These are validated/recoverable archive bytes, not release qualification. Official r2 failed its first draw. Public dce r3 succeeded warm but stalled cold; successful patched e69 diagnostics use a different binary and do not qualify the retained dce archives. Windows remains unexecuted. All meaningful failure/original evidence remains.

Retain **every ZIP, both Linux raw PCKs, all manifests/SUMS, logs, captures, users/caches, source clone, engines, R6/art and unrelated build siblings**. There is no directory deletion. The map preserves original file and directory modes; 71 files have a recorded disk/ZIP mode difference, so recovery applies `disk_mode`, not ZIP permissions. Exact compiled bytes depend on these retained ZIPs; Git source alone does not guarantee identical PCKs. Timestamps are pre-removal drift checks, not a restoration promise.

## Guard and recovery

[verify-only.json](verify-only.json) records 114 verified files and zero removals. The guard defaults to verification, enforces the exact three expanded roots plus exactly two standalone paths, checks all archived/file hashes and metadata, and scans accessible same-user process references. Expanded inventories must match exactly; unrelated siblings of the two standalone PCKs are permitted and untouched. It refuses inaccessible owned process entries or live references. This is not a machine-wide idle proof.

From `/workspace/ANDOLAN`, use a fresh report path:

```sh
env PYTHONDONTWRITEBYTECODE=1 taskset -c 4 python3 \
  docs/evidence/desktop-finish-r3-expanded-cleanup-r1/guard.py \
  --report /tmp/yuga-r3-expanded-cleanup-recheck.json
```

**Unrun, for root only after separate approval:** replace the placeholder with the pushed 40-character checkpoint. The guard verifies that checkpoint is on the freshly observed remote branch and contains the exact map/audit/guard/ownership bytes before any unlink. It then repeats byte/mode/inode/link/time and process checks and removes only listed regular files.

```sh
env PYTHONDONTWRITEBYTECODE=1 taskset -c 4 python3 \
  docs/evidence/desktop-finish-r3-expanded-cleanup-r1/guard.py \
  --published-commit <REMOTE_VERIFIED_CHECKPOINT> --remove \
  --report /tmp/yuga-r3-expanded-cleanup-execution.json
```

For later recovery, verify the retained ZIP hash and named member, stream to an exclusively created temporary sibling, verify length/SHA-256, and apply the mapped `disk_mode`. Reject symlink ancestors or an existing destination. Link the temporary file to the missing destination with `os.link` so a concurrent new file cannot be overwritten, then remove the temporary sibling and recheck final bytes/mode. Directories remain; stop if any required directory is missing or changed. No extraction, restoration or removal was executed here.

## Corrected source-capacity calculation

The earlier r2 capacity estimate did not include the next checkout's Git growth. This new packet supersedes that estimate without editing its historical map or result.

- The owned clone is still `f8dec5fa`; all 2,732 mapped historical files remain absent and need 3,112,771,584 allocated bytes restored.
- Exact `f8dec5fa` → `d1bfbe28` adds 473 paths, 879,987,341 logical bytes, estimated 881,139,712 bytes rounded per file to 4 KiB. None of these additions already exists in the owned clone. [Full Git-tree delta](f8-to-d1-tree-delta.json).
- The lead's captured provisional allowlist now contains 577 files (updated from its initial 572): 83,568,925 logical /84,791,296 ceil4KiB bytes. Eleven are replacements; the net estimated addition is 84,484,096, but the budget conservatively charges the full 84,791,296. All captured allowlist hashes still matched during review. This is **not yet a committed target**. [Captured list](pending-checkpoint-allowlist.json) and [per-path calculation](pending-checkpoint-delta.json).
- Add 4 MiB for this small packet/late reviews and 128 MiB reserve. At the map observation, `/tmp` had 2,926,358,528 free bytes. Both separately approved cleanup plans would add 1,358,299,136. After restoration, d1 growth, pending list and 4 MiB allowance, projected free space is 201,760,768: **67,543,040 bytes above the 128 MiB reserve**.
- Export to a fresh `/workspace/scratch/yuga-desktop-integrated-package-r4/build` using existing `--build-dir`, without another clone. At measurement `/workspace` had 2,805,833,728 free; the observed 784,232,448-byte build footprint leaves 2,021,601,280 bytes. Engine/runtime identity remains a separate decision.

[capacity-plan.json](capacity-plan.json) records all arithmetic. **Before restoring or checking out, recompute the actual final Git checkpoint delta and remeasure both filesystems.** Require enough space for restoration plus the final source growth plus 128 MiB reserve; stop if concurrent captures/art exhaust the margin. No checkout, source restoration, export or engine run was performed, and this packet does not authorize any of them.
