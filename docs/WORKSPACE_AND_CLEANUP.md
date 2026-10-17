# Cloud workspace and cleanup

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

The machine-readable receipt will be stored at [cloud-cleanup-2026-10-17.json](evidence/cloud-cleanup-2026-10-17.json). It distinguishes deleted duplicates/caches from retained local-only captures and records actual storage measurements. The receipt is an audit of this operation, not a blanket deletion policy for future sessions.

Reusable cloud settings should point new agents to `AGENTS.md` and `docs/START_HERE.md`, keep the tested installation script, and record the current checkout. Saving the draft does not publish a new environment snapshot. Review/save and Publish in environment settings activates the prepared snapshot; future processes still need to be started as documented.
