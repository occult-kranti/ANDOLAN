# Exact r2 expanded-package duplicate plan

**Prepared and verified only. No file has been removed.** Root must push this map and guard, verify the remote checkpoint, and then separately invoke removal. W1 and W6 released only the three listed inactive expansions; their ownership messages and the accessible-process observation are retained here.

The plan contains **102 regular files / 662,143,773 logical bytes / 662,401,024 allocated file bytes**:

| Exact root | Files | Allocated file bytes |
| --- | ---: | ---: |
| `/tmp/yuga-desktop-integrated-package-r2/build/yuga-native-linux-x86_64` | 34 | 209,657,856 |
| `/tmp/yuga-desktop-integrated-package-r2/build/yuga-native-windows-x86_64` | 34 | 243,085,312 |
| `/tmp/yuga-desktop-integrated-package-r2/extracted/yuga-native-linux-x86_64` | 34 | 209,657,856 |

Every expanded file matches its exact retained ZIP member SHA-256 and length. Both ZIP hashes match the archived r2 package receipt, and their inner manifests identify source `5542e61610d20e591effbed9dec15fd10398e31d`. That commit was verified as an ancestor of the actual remote production head `d1bfbe2` during this audit. **The ZIP bytes are validated and recoverable; this is not release qualification. The official r2 runtime failed its first-draw gate.** Its meaningful failure evidence remains archived and untouched.

The two ZIPs remain at r2 `build/yuga-native-{linux,windows}-x86_64.zip`, hashes `88948751…306a0` and `4c50c100…dfc7e`. They are the exact-byte recovery source for the engine/PCK and package contents. Git source alone does not promise reproduction of identical compiled PCKs. The ZIPs are retained local artifacts; pushing this recovery map does not remotely back up those archive bytes.

The map records original file modes, sizes, SHA-256, device/inode/link count, allocation and timestamps. **66 files have disk mode `0600` but ZIP mode `0644`.** Exact recovery therefore applies the mapped disk mode after reading the ZIP, rather than blindly using the archive mode. Four executable files remain `0755`. All directories and their modes are retained. Timestamps are recorded for pre-removal drift detection; no timestamp-identical restoration is claimed.

Only individual mapped files are proposed for removal. All ZIPs, raw PCKs, export/package manifests, extraction receipts, logs, user state, caches, source/art and unique evidence remain. Every r1/r3 expansion, current diagnostic, owned source clone, runtime and R6 path is outside this allowlist. There is no directory removal, broad cleanup, Git pruning, source restoration or export in this packet.

## Verification and later guarded removal

The existing individual-file cleanup pattern is retained: exact map hash, unchanged ZIP and file bytes/modes/metadata, complete allowed inventory, and a fresh accessible same-user process scan. The default guard is verify-only. It was executed successfully against all 102 files; [verify-only.json](verify-only.json) records zero removals. The initial audit expected the wrong inner-manifest key and stopped before writing a map; its small source/failure record remains separately preserved. The corrected audit checks `git.head` and clean native worktree status.

From `/workspace/ANDOLAN`, a fresh verification is:

```sh
env PYTHONDONTWRITEBYTECODE=1 taskset -c 4 python3 \
  docs/evidence/desktop-finish-r2-expanded-cleanup-r1/guard.py \
  --report /tmp/yuga-r2-expanded-cleanup-recheck.json
```

**Not executed:** after explicit root approval, replace the placeholder below with the pushed 40-character checkpoint containing these exact map/audit/guard/ownership bytes. The guard requires that checkpoint to be an ancestor of the freshly observed remote branch and validates those committed bytes before it can unlink anything. It aborts on any process holder, inaccessible owned process entry, changed file/archive, unsafe path or unlisted expanded file. Remote verification does not replace the root's execution decision.

```sh
env PYTHONDONTWRITEBYTECODE=1 taskset -c 4 python3 \
  docs/evidence/desktop-finish-r2-expanded-cleanup-r1/guard.py \
  --published-commit <REMOTE_VERIFIED_CHECKPOINT> --remove \
  --report /tmp/yuga-r2-expanded-cleanup-execution.json
```

The guard removes only the 102 mapped regular files and retains every directory. Save its execution receipt separately and record actual free space. Concurrent writes prevent attributing a raw filesystem free-space delta solely to this operation.

## Exact recovery, if later needed

For each missing mapped file, first verify the retained archive's full SHA-256 against `recovery-map.json`; reject any ZIP/member mismatch. Read the named `member` (not a filesystem extraction path), stream it to an exclusively created temporary sibling, and validate its length and SHA-256. Apply `int(disk_mode,8)` with `fchmod`. Reject symlink ancestors and any existing destination, then use `os.link(temp, destination)` followed by removal of the temporary sibling: creation fails if a new destination appears, so no changed user file is overwritten. Verify final content and mapped mode. Directories were retained; if a directory is missing or changed, stop rather than inventing a new restoration scope. No recovery command was executed.

## Space and source reuse

[W6's source-reuse plan](../../../games/yuga-native/docs/evidence/desktop-finish/package-next-source-reuse/W6-r1/PLAN.md) retains the existing `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN` checkout and its imports. Restore its exact 2,732 historical Git blobs only after W1 releases the clone and root authorizes restoration; do not create a duplicate full clone or hide missing files with Git flags. This is a separate 3,112,771,584-byte operation under the previously published map.

At this audit, `/tmp` had 3,300,028,416 bytes free and `/workspace` had 2,829,111,296. Even after this proposed cleanup, `/tmp` would be 68,792,320 bytes short of W6's 4,031,221,760-byte combined restoration/export/reserve floor. The recommended split is:

- Restore the existing source checkout in `/tmp`: after cleanup and restoration, estimated 849,657,856 bytes remain, including the 134,217,728-byte reserve.
- Use a fresh `/workspace/scratch/yuga-desktop-integrated-package-r4/build` through the existing package helper's `--build-dir`; the observed r3 build footprint is 784,232,448 bytes, leaving an estimated 2,044,878,848 bytes on the workspace filesystem before other writes.
- Keep exporter/runtime/provenance selection explicit and separately approved. This plan changes no engine identity or package semantics. It does not authorize any successor export or clone update.

[capacity-plan.json](capacity-plan.json) records the arithmetic. Remeasure both filesystems immediately before restoration/export; current captures and art may consume more space. No broader cleanup is proposed if the reserve is insufficient.
