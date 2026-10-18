Preparation only; no files have been removed. The fixed eleven untracked aliases occupy **171,704,653 logical bytes / 171,728,896 allocated bytes**. There is no attempt to reach an arbitrary 300 MB target.

The exact committed Backup A inventory supplies every candidate and recovery route. The larger 177+101 recent alias groups total only 12,566,189 logical bytes and include current release/frontage material, which is excluded. This proposal selects only three old duplicate R4 candidate GLBs, four old uncompressed pose/draw JSON files recoverable from committed gzip, and three rejected-R6 duplicate baseline PNGs plus one duplicate import JSON. W1/W2 explicitly released the listed filenames; W3 confirmed no inventory overlap. `ownership.json` records those dispositions and their limits.

`audit.py` verifies source-map bytes at remote-backed commit `37bb953503a1a374f7c0c6aae1ef3d43cfba8867`, all eleven local hashes/modes and single-link regular-file identities, absence from the current Git index, exact committed recovery blobs and decompression where required. It checks accessible live process argv/file descriptors/maps. Defunct processes cannot retain live file descriptors; inaccessible other-UID processes are recorded as an inspection limit. An inaccessible live process owned by the current user fails the audit. Current art/capture paths, canonical runtime, r4 release/public/extracted runtime, unique originals, ambient caches and user state are not candidates.

Default verification (fresh report path):

```sh
taskset -c 3 python docs/evidence/desktop-finish-inactive-alias-cleanup-r1/guard.py --report /workspace/scratch/NEW-alias-verify.json
```

Only after root approval and exact remote backup of this packet, root may invoke the same guard with `--remove --published-commit FULL_COMMIT --confirm-owner-release` and a fresh report path. The guard checks remote ancestry and exact published map/audit/guard/ownership/README bytes, repeats all file/recovery/index/process checks, then removes only the eleven named files. It never removes directories. Each removed path retains exact size/mode/hash and recovery instructions in the execution receipt; partial failure also records already removed paths. The owner-confirmation flag requires root to re-confirm that no work resumed on these names.

Restoration: read `git_blob` from the named `recovery.commit`/`recovery.path` into a separate destination; for `gzip_decompress`, decode that retained gzip without altering it. Require the original byte count, SHA-256 and Git blob ID, apply `restore_mode`, and write the exact original path only if absent. Never overwrite differing content. Rehydrate aliases before replaying old receipts that address these names. These are content aliases, not transferred visual acceptance.

The initial observed workspace availability was about 1.18 GB. This proposal adds about 171.7 MB, rather than promising current free space or a final motion budget. The 500 MiB reserve must be rechecked alongside the exact upcoming raw-plus-archive cost and concurrent writes. Do not touch the already completed r4 expanded cleanup again.
