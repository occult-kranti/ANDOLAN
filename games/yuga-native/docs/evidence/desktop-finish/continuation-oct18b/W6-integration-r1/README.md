# Two original ZIP aliases — recovery preparation

Only the two original build ZIP aliases listed in zip-alias-map.json are selected. Fresh W3 public downloads remain retained. Both archives were freshly hashed: Linux 781d904d…88aa8 and Windows 8051586f…01c8, identical to the sealed public audit and qualified package. Candidates are regular nlink1 files, distinct from the retained public inodes. Selected logical bytes: 244,104,795; allocated bytes: 244,117,504.

W1, W3, W6 and root released only these inactive aliases. W3 has no current/planned public-download writes. The accessible process probe found no selected-file references; inaccessible PIDs and the inspection limit are retained in the map/check report. Keep all other paths, including all five public downloads, original build metadata/Linux PCK, W1 actual extraction, source/private caches, captures, meaningful failures and user state.

Recovery: copy the row’s exact retained public path back to its original candidate path, require recorded SHA-256 and length, then restore its recorded mode. Each row also records the exact public release URL and asset ID; a future remote download must pass the same SHA-256/length before use. No extraction/re-export is required to recover a ZIP alias.

46/46 bounded source/predicate controls passed; no engines, Git/network calls or candidate mutations were performed. The full local preparation/check freshly rehashed both aliases, all five public files, original build metadata/Linux raw PCK and actual extracted Linux PCK/runtime. No deletion has occurred.

Root must back up this direct packet plus the exact prior public-audit and package qualification receipts on a remotely verified backup branch before explicit removal authorization. The guard independently checks the exact remote ref and backed map/helper/owner/audit/qualification blobs before deleting. Only two fixed candidate paths can pass. Removal records each unlink atomically; no directory or recursive removal exists.

Literal read-only check:

```sh
python3 -B games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/zip-aliases.py --plan /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/zip-alias-map.json --plan-sha256 ad6ba0a37980ddc786f174bd985dd6c42249a62a60310c4c7cea34d78ba9696a --report /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/fresh-pre-removal-check.json
```

The authorized removal invocation adds `--remove --backup-commit EXACT_REMOTE_BACKUP --backup-branch EXACT_BACKUP_BRANCH` and uses a fresh `execution.json` report. Those backup identities are deliberately unset until root confirms them. Read-only checks do not call Git or the network.
