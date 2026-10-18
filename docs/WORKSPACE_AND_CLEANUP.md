# Cloud workspace and cleanup

Desktop S2 evidence cleanup: [receipt](evidence/desktop-finish-s2-raw-cleanup.json) records15 raw trace duplicates removed after their lossless gzip versions were pushed and remote-verified at `31ca18948c691c31719c92afd3245e75cea8c8d1`. Every uncompressed byte/hash was checked against the committed gzip. This freed another106,905,600 allocated workspace bytes; all samples, failed controls and source remain recoverable. The former scratch path is no longer required by the trace reader.

Latest desktop cleanup: [verified receipt](evidence/desktop-finish-storage-cleanup.json) records 156 byte-identical files across eight historical expanded package directories and two duplicate public ZIPs. It freed **1,496,768,512 allocated bytes in the workspace**; the remaining duplicate ZIP bytes were on the separate `/tmp` filesystem. All retained ZIPs, source/art, captures, logs/manifests, tools/caches and user files remain. Remote source `0fb96d1` was verified before deletion; the receipt records every recovery path and file hash.

Current UI/visual cleanup: [cache receipt](evidence/ui-campaign-cache-cleanup.json) removes six inactive U2 import caches (402,627,331 logical bytes). [Proposal duplicate receipt](evidence/visual-proposal-duplicate-cleanup.json) removes399 inactive proposal files (3,019,440,269 logical bytes), each identical to a Git blob at remote-verified `00a204bfbf5e1de47a0a12a233841d7f3a2475ab`. All71 unique rejected/manifests/support files remain; accepted R7 proposal and active captures remain whole. Partially retained proposal trees must restore the listed exact files before re-execution.

Current round cleanup: [R2 cache receipt](evidence/visual-round2-cache-cleanup.json) records 13 obsolete Godot import caches removed after checkpoint6046171 was pushed and remote-verified. About895MB of regenerable cache bytes were removed; all source, original frames, failure evidence, installed tools and active caches remain.

Latest visual-campaign cleanup: [verified receipt](evidence/visual-campaign-cleanup/README.md).
Nine obsolete render-clone/cache paths were removed after source `09dac722`
was pushed and all recovery bytes were checked: about **793 MB logical /
806 MB allocated**. Current renders, all raw frames, source art and installed
tools remain. Earlier cleanup receipts below describe separate operations.

Rama preview cleanup on 17 October 2026: [the verified receipt](../games/yuga-native/docs/evidence/rama-hero/published/cleanup/receipt.json) removes 2.2 GB of obsolete duplicate package ZIPs/extractions after the current public release was downloaded and verified. Current R3/public downloads and all source, art and accepted/rejected capture evidence remain. Superseded package manifests retain exact regeneration commits.

The cloud worker is a development machine; Git and published releases retain the durable project history. Preserve the ready toolchain while removing duplicate delivery artifacts. The [build handbook](../games/yuga-native/docs/BUILD_HANDBOOK.md) supplies setup/rebuild commands, and [START_HERE](START_HERE.md) supplies product routing.

## Directory ownership

| Location | Purpose and retention |
| --- | --- |
| `/workspace/ANDOLAN` | The existing Git checkout. Keep source, `.git`, notices, source art, accepted evidence and local user changes. Do not reorganize runtime paths merely to make the root shorter. |
| `/workspace/tooling/native-engine` | Verified installed Godot Linux/Windows engines and installation manifest. Download ZIPs are disposable when installed payloads are verified; the official installer downloads and checks them again when needed. |
| `/workspace/tooling/native-render` | Xvfb/Mesa runtime and its setup metadata. Keep libraries needed for real rendering. |
| `/workspace/tooling/yuga-native-python` | Pinned NumPy/SciPy environment. Keep it ready for audio/media tests. |
| Repository `node_modules/` and native `.godot/` | Rebuildable, but retained for quick resumption. `npm ci` and Godot import can restore them. They are excluded from Git and releases. |
| `/workspace/scratch/yuga-retained` | Explicitly retained raw capture frames and small diagnostics that are not fully represented by remote bytes. Its local inventory explains retention. This is local-only material, not proof of remote backup. |
| Fresh `/tmp/yuga-*` outputs | Short-lived test, capture, export and download staging. Use unique names; archive accepted results before cleanup. |
| `/workspace/shared`, `/workspace/library-files`, platform logs | Platform/user-owned areas. Leave them alone unless their ownership and recoverability are established. |

No whole checkout is removed or moved by this cleanup. Git history and accepted source-pinned evidence stay at their existing paths. Extra downloads are not evidence that a tool was configured or exercised; the research brief identifies actual studies.

## Cleanup procedure

1. Record local HEAD/status, read the actual remote branch/tag, and verify the intended checkpoint is pushed. A local commit alone is not a remote backup.
2. Inventory each candidate with bytes, category and recovery route. Resolve symlinks; do not follow a candidate into an unrelated directory. Inspect active processes/open files and coordinate with workers.
3. For exact duplicates, compare bytes/hashes with committed evidence or the public release manifest. Preserve unique small export manifests/logs before deleting a package directory. A local PCK may differ from CI imports even when gameplay sources match.
4. Keep unique source art, credentials/user saves, meaningful unarchived diagnostics and full raw frames unless deliberately retained elsewhere or independently backed up. Record any local-only retention explicitly.
5. Delete only the reviewed path allowlist. Do not run broad `git clean -fdx`, erase `/tmp`, prune all caches indiscriminately or remove installed dependencies to chase a larger number.
6. Record removed bytes and retained paths, then validate Git state, tool versions and a representative development check. Commit/push the receipt and update the saved cloud start instructions.

The reproducible recovery route for current public delivery files is the [traversal/army release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17). Verify downloads against its `SHA256SUMS`, `release-manifest.json` and the tagged source before executing. Package preparation can also be rerun using the handbook. Never describe a newly rebuilt artifact as byte-identical without checking it.

## This cleanup

The completed cleanup removed **1,408,483,328 allocated bytes (about 1.41 GB)** from 18 audited paths. Installed engines, rendering libraries, Python dependencies, Node dependencies and Godot imports remain. Unique raw render and diagnostic material was moved with exact SHA verification into `/workspace/scratch/yuga-retained` (116,492,110 logical bytes, locally retained only). Six small package metadata/log files were pushed before deleting local package copies.

The machine-readable receipt is stored at [cloud-cleanup-2026-10-17.json](evidence/cloud-cleanup-2026-10-17.json). It distinguishes deleted duplicates/caches from retained local-only captures and records actual storage measurements. The receipt is an audit of this operation, not a blanket deletion policy for future sessions.

Reusable cloud settings should point new agents to `AGENTS.md` and `docs/START_HERE.md`, keep the tested installation script, and record the current checkout. Saving the draft does not publish a new environment snapshot. Review/save and Publish in environment settings activates the prepared snapshot; future processes still need to be started as documented.

On 18 October 2026, two rejected package expanded folders were removed only after all 58 files matched retained ZIP payloads byte for byte, freeing 451,857,282 bytes. Both rejected ZIPs, raw PCKs, manifests and logs remain. See [receipt](evidence/rejected-package-expanded-cleanup.json).

On 18 October 2026, the two final UI package expanded build folders were removed after all58 files matched the retained qualified ZIPs byte for byte and live owned processes had no references. This removed451,869,714 logical bytes (452,034,560 allocated file bytes). Public release downloads, both ZIPs/raw PCKs, all manifests/logs, source/caches and the actual native-capture extraction remain. File and directory modes are recorded for exact recovery. See [receipt](evidence/ui-final-expanded-package-cleanup.json).
