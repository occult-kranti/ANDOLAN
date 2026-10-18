# Cloud workspace and cleanup

Updated 18 October 2026. Start with the [active desktop handoff](../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md) for current source, package and worker ownership. The cloud is a development machine; pushed Git history and published releases provide durable recovery. A saved cloud configuration draft does not back up filesystem bytes.

## Current state

The active desktop campaign has reclaimed **12,942,286,848 allocated file bytes** through separately recorded operations. This is historical reclamation, not current free space or a sum of every cleanup in the repository. Later source restoration consumes storage again. Only inactive, exactly recoverable duplicates were removed. Current runtime, accepted and rejected art, original captures, meaningful failure evidence, tools, caches and user state remain.

The second 18 October continuation removed two inactive build ZIP aliases after recovery backup `36310607592cd27e1d15b63660b1cbaf51e3b6de`, reclaiming **244,117,504 allocated bytes**; [exact execution](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/execution.json). It then removed the single inactive build Linux raw PCK after backup `097a10296760f72b4e0cc4a1243e996bb5ba93cc`, reclaiming **70,602,752 allocated bytes**; [recovery map](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/raw-pck-recovery-r1/recovery-map.json) and [execution](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/raw-pck-recovery-r1/execution.json). The independently downloaded public ZIPs, their exact recovery member, actual extracted PCK/runtime, metadata, caches and unique work remain. The earlier paragraphs below describe historical retention at each operation; the new raw-PCK map owns the later removal of that one build copy.

The earlier [polish package cleanup](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2-duplicates/execution.json) removed exactly 82 ZIP-backed staging files and the duplicate Windows raw PCK, reclaiming 470,986,752 allocated bytes after map/helper/owner/qualification backup `cef6d8c53b7278e9dc824299661de1b0775a4ad2` was pushed and verified. Both qualified ZIPs, Linux raw PCK, actual extraction, source/cache, original captures and user state remain. The new release and all five public files were independently verified afterward.

The earlier r2/r3 expanded-package cleanup removed 216 exact duplicate files after the recovery maps were pushed in `96d5b9cd`: 662,401,024 and 695,898,112 allocated bytes. ZIPs, Linux raw PCKs, unique metadata and actual captures remain. [r2 execution](evidence/desktop-finish-r2-expanded-cleanup-r1/execution-receipt.json) and [r3 execution](evidence/desktop-finish-r3-expanded-cleanup-r1/execution-receipt.json) record each identity and archive recovery route.

The [r4 cleanup](evidence/desktop-finish-r4-expanded-cleanup-r1/execution-receipt.json) removed 80 exact expanded-package/Windows-PCK duplicates, reclaiming 469,565,440 allocated bytes after the recovery map and independent public audit were pushed in `37bb953503a1a374f7c0c6aae1ef3d43cfba8867`. Actual extracted runtime, all five release files, Linux PCK, logs, captures and unique source remain.

The latest [inactive-alias cleanup](evidence/desktop-finish-inactive-alias-cleanup-r1/execution-receipt.json) removed 11 untracked historical duplicates, reclaiming 171,728,896 allocated bytes after the exact selection and guard were pushed in `0412db42f0a3da8afa1c30b33be6239d04f7afe8`. Three old R4 GLBs, four uncompressed pose reports and four R6 baseline aliases remain recoverable from exact committed blobs or gzip. Current art, original selected captures and release files are untouched.

The earlier [package-source cleanup](evidence/desktop-finish-package-source-cleanup-r1/execution-receipt.json) removed 2,732 historical files from `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN`. Those files were subsequently restored byte-for-byte before r4 export. The checkout is now clean detached `96d5b9cd` with 18,038 tracked files; the [r4 source/export receipt](../games/yuga-native/docs/evidence/desktop-finish/package-export-r4/W6/receipt.json) records restoration and before/after integrity. Do not repeat recovery using the obsolete partial-state marker. Other historical partial trees still require their own exact maps before reuse.

The [inactive art backup](../games/yuga-native/docs/evidence/desktop-finish/inactive-art-backup-r1/README.md) is pushed at `d1bfbe28850899aba12226227bc5d567a50a3bcb`. It preserves rejected hair R4/R5 and source-only shoulder work. Its exact duplicate mappings explain intentionally omitted local copies. The [37bb953 backup](../games/yuga-native/docs/evidence/desktop-finish/backup-after-96d5-r1/README.md) adds rejected R6, the generated concept, editable continuous-hair clay, source/native frontage candidate, AO diagnostic and exact r4 publication evidence. Its recovery maps preserve intentionally omitted duplicate paths. [Backup 0412db4](../games/yuga-native/docs/evidence/desktop-finish/backup-after-37bb-r1/README.md) adds the first actual frontage and clay rejections, framing corrections and their editable sources. An untracked status never makes a file disposable.

## Directory ownership

| Location | Purpose and retention |
| --- | --- |
| `/workspace/ANDOLAN` | User checkout. Preserve source, `.git`, notices, art, accepted/rejected evidence and local changes. Do not move runtime paths for cosmetic organization. |
| `/opt/godot/4.6.3` and `/workspace/tooling/native-engine` | Installed official exporter/runtime tools and installation metadata. Keep them ready. |
| `/workspace/tooling/godot-public-4.6.3` | Separately identified public template binaries. Preserve source/build/license provenance; patched and unmodified variants have different hashes. |
| `/workspace/tooling/native-render` and `/workspace/tooling/yuga-native-python` | Rendering libraries and pinned Python environment. Keep required dependencies. |
| Repository `node_modules/` and native `.godot/` | Rebuildable dependencies/imports, retained for fast resumption. Excluded from source and release payloads. |
| `/workspace/scratch/yuga-retained` | Explicit local-only raw frames/diagnostics. Its inventory is retention evidence, not proof of remote backup. |
| New `/workspace/scratch/yuga-*` outputs | Owned test, capture, export and download staging, including XDG/cache state. `/tmp` is near its reserve floor; keep new bulk output on `/workspace`. Use unique paths, check owners and archive results before cleanup. Some historical `/tmp` trees remain intentionally partial. |
| `/workspace/shared`, `/workspace/library-files`, platform logs, user `.design/` and scratch | Leave unchanged unless ownership and recoverability are established for exact requested paths. |

The `/workspace` and `/tmp` filesystems differ. Cross-device hardlinks do not work; do not substitute symlinks where package guards require regular files. Plan restoration, export and capture reserves before copying another full checkout.

## Cleanup procedure

1. Inspect local branch/HEAD/status and the actual remote ref. Verify the intended source and recovery map are pushed; a local commit is not a remote backup.
2. Inventory exact candidate paths, bytes and recovery routes. Do not follow symlinks into unrelated trees. Coordinate with every current owner and inspect accessible process files/maps; record inspection limits.
3. Compare duplicate bytes and file modes against retained archive members or exact committed Git blobs. Keep unique export logs/manifests. CI and local PCK bytes may differ despite the same gameplay source.
4. Preserve unique art, credentials, saves, original frames and meaningful failure diagnostics unless they are deliberately backed up elsewhere. State local-only retention honestly.
5. Delete only the reviewed allowlist after a final identity/ownership check. No broad `git clean -fdx`, `/tmp` erasure, cache wipe or Git pruning.
6. Record actual deleted bytes and retained paths. Push the execution receipt and update the handoff/cloud draft. Run a relevant development check only when cleanup could affect it.

Use the [build handbook](../games/yuga-native/docs/BUILD_HANDBOOK.md) to regenerate dependencies and packages. A rebuilt artifact is not byte-identical unless checked. Use each release's own checksum manifest and source identity for downloads; the [current desktop polish preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-desktop-polish-2026-10-18) is exact source `79e5c15d`. The older UI `9e81a7c` preview is historical; source backup commits do not relabel either executable.

## Recovery records

These records describe separate operations. Some contain cumulative figures; do not add their totals blindly.

| Operation | Exact evidence |
| --- | --- |
| 82 new polish staging/Windows-PCK duplicates: 470,986,752 allocated bytes | [Map](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2-duplicates/recovery-map.json), [execution](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2-duplicates/execution.json); exact recovery backup cef6d8c before deletion |
| 182 inactive capture-project asset copies: 1,034,743,808 allocated bytes | [Map](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/recovery-map.json), [execution](../games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/storage-execution.json); map pushed in d199f607 before deletion |
| Eleven inactive historical aliases: 171,728,896 allocated bytes | [Map](evidence/desktop-finish-inactive-alias-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-inactive-alias-cleanup-r1/execution-receipt.json) |
| r4 expanded packages and duplicate Windows PCK:469,565,440 allocated bytes | [Map](evidence/desktop-finish-r4-expanded-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-r4-expanded-cleanup-r1/execution-receipt.json) |
| r3 expanded packages and r2/r3 duplicate Windows PCKs:695,898,112 allocated bytes | [Map](evidence/desktop-finish-r3-expanded-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-r3-expanded-cleanup-r1/execution-receipt.json) |
| r2 expanded packages: 662,401,024 allocated bytes | [Map](evidence/desktop-finish-r2-expanded-cleanup-r1/recovery-map.json), [execution](evidence/desktop-finish-r2-expanded-cleanup-r1/execution-receipt.json) |
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

The [current cloud setup handoff](evidence/desktop-continuation-cloud-r1/CURRENT_SETUP.md) points to the current user repository and start instructions; four third-party reference checkouts are excluded from project membership. Installation/network/credential configuration is preserved. Saving the draft does not publish a snapshot or establish fresh-task restoration. Environment Settings → Save → Publish activates it; future processes still need to be started as documented.

New agents should read `AGENTS.md` → [START_HERE](START_HERE.md) → the active subsystem handoff, rather than scanning the entire evidence archive. Context compaction is platform-managed.

The [two public r4 ZIP aliases](evidence/desktop-finish-r4-public-zip-cleanup-r1/execution-receipt.json) were removed only after fresh local hashes, exact public API identities, retained independent public-download verification and owner/FD checks. This reclaimed 243,978,240 allocated bytes. The adjacent recovery map preserves exact download URLs, sizes, SHA-256 values and modes. Actual Linux extraction, raw Linux PCK, package manifests, unique sources and evidence remain local.

The [single raw-motion cleanup](../games/yuga-native/docs/evidence/desktop-finish/next-motion/root-motion-raw-cleanup-r1.json) removed only inactive scratch `capture.json` after exact decompression against its remotely backed `ca52cbd` gzip and fresh owner/inode/hash/process checks. It reclaimed 16,687,104 allocated bytes; all original PNGs, compressed exact pose data, sources and caches remain. The three further proposed raw outputs were initially retained, then removed only after the separate exact backup below.

After the exact `eb39ea6` source/evidence backup was pushed and remotely verified, [three inactive private-motion JSON reports](../games/yuga-native/docs/evidence/desktop-finish/next-motion/root-motion-private-raw-cleanup-r1.json) were removed after renewed hash, inode, lossless decompression and ownership checks. This reclaimed another 21,430,272 allocated bytes; their exact compressed reports remain committed. No original image, editable source, cache or user state was removed.
