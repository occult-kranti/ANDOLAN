# r4 expanded-package duplicates: prepared, not deleted

This packet covers exactly **80 regular files**, **469,341,307 logical bytes** and **469,565,440 allocated file bytes**. Scope is the two build payload directories under `/workspace/scratch/yuga-desktop-integrated-package-r4/build/` (`yuga-native-linux-x86_64`, `yuga-native-windows-x86_64`) and the standalone `yuga-native-windows.pck` only. It excludes the actual W1 extraction. All five release files, Linux raw PCK, logs, manifests, provenance, captures, caches, user state, source and unique evidence remain.

Every candidate file was read and compared byte-for-byte by size/SHA-256 with its exact retained ZIP member; every ZIP member was read through CRC verification. Linux has 45 members, Windows 34; the additional standalone Windows PCK equals its Windows ZIP member. Both retained ZIP hashes equal the final r4 qualification and the independently downloaded public assets at source `96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12`, release `416367666`. The [public audit reference](public-audit-reference.json) pins W5's passed five-asset verification. No new download or engine ran here.

[Ownership](ownership.json) records explicit W1/W6 release of only these build duplicates. The [process observation](process-observation.json) found no candidate references and no inaccessible owned entries among accessible same-UID processes; this is not a global machine-idle claim. All files have one hardlink. The map records device/inode, allocation, mode and timestamps. **77 disk permissions differ from ZIP permissions**; recovery must apply each recorded `disk_mode`, not assume the ZIP mode reproduces the expanded folder. Directory paths/modes are retained and directories are never deleted. Timestamps are evidence metadata, not promised recovery properties.

The reviewed r3 audit/guard was reused with only fixed r4 paths/counts/source/archive pins, public-audit binding, workspace-space reporting, and protected-build-file checks. [reuse.patch](reuse.patch) shows the exact adaptation. `audit.py` generated the map read-only. The default guard verified **80/80**, removed **0**, and rehashed all protected build files before/after. No restoration-capacity framework or blanket cleanup was added.

Root may invoke removal only after independently reviewing this packet, committing/pushing the exact recovery map/guard/ownership/public reference **and the pinned public download-verification.json**, and explicitly authorizing execution. The guard checks remote ancestry and committed bytes, repeats every file/archive/mode/metadata/process check, then unlinks only each mapped regular file. It records removed paths and rechecks protected build identities. The command below is documentation, not an executed operation:

```sh
python3 -B docs/evidence/desktop-finish-r4-expanded-cleanup-r1/guard.py \
  --remove --published-commit <exact-pushed-map-commit> \
  --report docs/evidence/desktop-finish-r4-expanded-cleanup-r1/execution-receipt.json
```

Recovery uses `recovery-map.json`: verify the retained ZIP hash, read each exact `member`, restore only its mapped `root/path`, check bytes/SHA-256, and apply `disk_mode`. For a partial deletion, refuse to overwrite existing files; validate existing matches first. The source Git commit proves provenance but cannot recreate an identical compiled PCK without the retained ZIP. No original capture or current extracted runtime is a recovery input for this cleanup.

At inventory, workspace free space was 1,081,597,952 bytes. The proposed allocation reclaim is 469,565,440 bytes; concurrent work can change the eventual free-space delta. `/tmp` is untouched. **Status: prepared and verified only; no deletion.**
