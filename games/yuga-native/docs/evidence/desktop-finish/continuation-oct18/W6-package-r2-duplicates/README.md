# Exact successor staging duplicate recovery

This proposal selects82 newly generated r2 files:46 Linux and35 Windows expanded staging members plus the duplicate raw Windows PCK. They occupy470,986,752 allocated bytes. Every selected regular file has one link and matches its exact retained qualified ZIP member; the map pins path, SHA-256, length, mode, device/inode, mtime, link count, allocation, ZIP identity, member and CRC. No directory is selected.

`verification.json` passed82/82 without deleting anything. `guard-checks.json` passed20 finite namespace, inode and backup rejection checks. `owner-release.json` records W6 ownership and W1’s explicit release: actual runs use the separate W1 extraction. Accessible process references are empty; inaccessible process IDs are disclosed in the probes rather than represented as inspected.

Both ZIPs, Linux raw PCK, manifests, all proofs/logs, private snapshot/cache, failed r1, canonical source, W1 extraction, user state and captured originals remain protected. Root first backs this entire packet and the exact qualified receipt on `backup/yuga-desktop-polish-recovery-2026-10-18` using a private index, preserving canonical HEAD/index79e5. No deletion occurred during preparation.

After remote backup and root’s explicit execution instruction, the guard requires that exact backup tip and byte-identical guard/map/owner-release/qualification Git blobs. It repeats ZIP/retained/candidate/process checks before unlinking only mapped regular files, records partial removals and retains directories. The command is:

```sh
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2-duplicates/duplicates.py --plan /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2-duplicates/recovery-map.json --plan-sha256 41ba11269bca7661ba2ce1c0e8ae23f8f9c69ad833e5877c51d49910a9e46371 --report /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2-duplicates/execution.json --remove --backup-branch backup/yuga-desktop-polish-recovery-2026-10-18 --backup-commit "$YUGA_DUPLICATE_BACKUP_COMMIT"
```

Root supplies `YUGA_DUPLICATE_BACKUP_COMMIT` from the verified remote backup. Without `--remove`, the guard only verifies; use a fresh report name. No export, import or renderer is needed.

To recover one selected file, verify its retained ZIP’s recorded outer hash, read the exact member through EOF (CRC), confirm recorded length and SHA-256, create the original path exclusively, then apply its recorded filesystem mode. Do not overwrite a later file. Full recovery needs up to471MB, so budget space before restoring all82 duplicates.

The initial receipt preceded the README because its first shell write used the wrong working directory. `receipt-before-readme.json` preserves that incomplete inventory; final `receipt.json` includes this README. Neither preparation removed any file.
