# Cloud workspace and cleanup

Updated 18 October 2026. Start with the [active desktop handoff](../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md) for current source, package and worker ownership. The cloud is a development machine; pushed Git history and published releases provide durable recovery. A saved cloud configuration draft does not back up filesystem bytes.

## Current state

The active desktop campaign has reclaimed **8,840,146,944 allocated file bytes** through separately recorded operations. This is historical reclamation, not current free space or a sum of every cleanup in the repository. Later source restoration consumes storage again. Only inactive, exactly recoverable duplicates were removed. Current runtime, accepted and rejected art, original captures, meaningful failure evidence, tools, caches and user state remain.

The latest [package-source cleanup](evidence/desktop-finish-package-source-cleanup-r1/execution-receipt.json) removed 2,732 historical files from `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN` after export and owner release. The checkout is intentionally partial. Its retained runtime/PCK is usable for the declared package diagnostics; **restore the exact mapped Git blobs before any full-source export**. Do not hide missing source with a packaging ignore rule. The [recovery map](evidence/desktop-finish-package-source-cleanup-r1/recovery-map.json) records identities and modes.

The [inactive art backup](../games/yuga-native/docs/evidence/desktop-finish/inactive-art-backup-r1/README.md) is pushed at `d1bfbe28850899aba12226227bc5d567a50a3bcb`. It preserves rejected hair R4/R5 and source-only shoulder work. Its exact duplicate mappings explain intentionally omitted local copies. R6 hair is separate current work; an untracked status never makes a file disposable.

## Directory ownership

| Location | Purpose and retention |
| --- | --- |
| `/workspace/ANDOLAN` | User checkout. Preserve source, `.git`, notices, art, accepted/rejected evidence and local changes. Do not move runtime paths for cosmetic organization. |
| `/opt/godot/4.6.3` and `/workspace/tooling/native-engine` | Installed official exporter/runtime tools and installation metadata. Keep them ready. |
| `/workspace/tooling/godot-public-4.6.3` | Separately identified public template binaries. Preserve source/build/license provenance; patched and unmodified variants have different hashes. |
| `/workspace/tooling/native-render` and `/workspace/tooling/yuga-native-python` | Rendering libraries and pinned Python environment. Keep required dependencies. |
| Repository `node_modules/` and native `.godot/` | Rebuildable dependencies/imports, retained for fast resumption. Excluded from source and release payloads. |
| `/workspace/scratch/yuga-retained` | Explicit local-only raw frames/diagnostics. Its inventory is retention evidence, not proof of remote backup. |
| Fresh `/tmp/yuga-*` outputs | Owned test, capture, export and download staging. Use unique paths, check owners and archive results before cleanup. Some historical trees are intentionally partial. |
| `/workspace/shared`, `/workspace/library-files`, platform logs, user `.design/` and scratch | Leave unchanged unless ownership and recoverability are established for exact requested paths. |

The `/workspace` and `/tmp` filesystems differ. Cross-device hardlinks do not work; do not substitute symlinks where package guards require regular files. Plan restoration, export and capture reserves before copying another full checkout.

## Cleanup procedure

1. Inspect local branch/HEAD/status and the actual remote ref. Verify the intended source and recovery map are pushed; a local commit is not a remote backup.
2. Inventory exact candidate paths, bytes and recovery routes. Do not follow symlinks into unrelated trees. Coordinate with every current owner and inspect accessible process files/maps; record inspection limits.
3. Compare duplicate bytes and file modes against retained archive members or exact committed Git blobs. Keep unique export logs/manifests. CI and local PCK bytes may differ despite the same gameplay source.
4. Preserve unique art, credentials, saves, original frames and meaningful failure diagnostics unless they are deliberately backed up elsewhere. State local-only retention honestly.
5. Delete only the reviewed allowlist after a final identity/ownership check. No broad `git clean -fdx`, `/tmp` erasure, cache wipe or Git pruning.
6. Record actual deleted bytes and retained paths. Push the execution receipt and update the handoff/cloud draft. Run a relevant development check only when cleanup could affect it.

Use the [build handbook](../games/yuga-native/docs/BUILD_HANDBOOK.md) to regenerate dependencies and packages. A rebuilt artifact is not byte-identical unless checked. Use each release's own checksum manifest and source identity for downloads; the [current public UI preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18) remains distinct from newer source and held draft artifacts.

## Recovery records

These records describe separate operations. Some contain cumulative figures; do not add their totals blindly.

| Operation | Exact evidence |
| --- | --- |
| Latest historical package-source duplicates: 3,112,771,584 allocated bytes | [Recovery map](evidence/desktop-finish-package-source-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-package-source-cleanup-r1/execution-receipt.json) |
| Four inactive roof/overview source children: 728,309,760 allocated bytes | [Map](evidence/desktop-finish-package-reserve-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-package-reserve-cleanup-r1/execution-receipt.json) |
| Historical capture-source duplicates: 3,064,627,200 allocated bytes | [Map](evidence/desktop-finish-old-source-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-old-source-cleanup-r1/execution-receipt.json) |
| Inactive public extractions: 330,764,288 allocated bytes | [Receipt](evidence/desktop-finish-historical-public-cleanup.json), [independent review](evidence/desktop-finish-historical-public-cleanup-W6.json) |
| Desktop trace gzip duplicates: 106,905,600 allocated bytes | [Receipt](evidence/desktop-finish-s2-raw-cleanup.json) |
| Desktop expanded package and ZIP duplicates | [Receipt](evidence/desktop-finish-storage-cleanup.json) |
| Earlier UI final expanded packages | [Receipt](evidence/ui-final-expanded-package-cleanup.json) |
| Earlier rejected expanded packages | [Receipt](evidence/rejected-package-expanded-cleanup.json) |
| UI imports and inactive visual proposals | [Cache receipt](evidence/ui-campaign-cache-cleanup.json), [proposal receipt](evidence/visual-proposal-duplicate-cleanup.json) |
| Earlier visual rounds | [R2 cache receipt](evidence/visual-round2-cache-cleanup.json), [campaign cleanup](evidence/visual-campaign-cleanup/README.md) |
| Rama preview delivery duplicates | [Receipt](../games/yuga-native/docs/evidence/rama-hero/published/cleanup/receipt.json) |
| Initial cloud cleanup and local-only retained diagnostics | [Receipt](evidence/cloud-cleanup-2026-10-17.json) |

## Reusable setup

The [latest cloud configuration draft](evidence/desktop-finish-current-cloud-r2/README.md) points to the current user repository and start instructions; four third-party reference checkouts are excluded from project membership. Installation/network/credential configuration is preserved. Saving the draft does not publish a snapshot or establish fresh-task restoration. Environment Settings → Save → Publish activates it; future processes still need to be started as documented.

New agents should read `AGENTS.md` → [START_HERE](START_HERE.md) → the active subsystem handoff, rather than scanning the entire evidence archive. Context compaction is platform-managed.
