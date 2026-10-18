# Package-source duplicate recovery plan — no deletion performed

Recommend removing only the **2,732 individually listed historical art/evidence files** in [recovery-map.json](recovery-map.json), after the ownership and package gates below close. They occupy **3,112,771,584 allocated file bytes (2.90 GiB)**, with 3,107,146,071 logical bytes. This is a plan, not execution authorization. The source clone remains intact and active.

The target is exclusively `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN`. `/tmp` is a separate filesystem from `/workspace`; this would recover `/tmp` capacity. At inspection, `/tmp` had about 1.6 GB available and the workspace overlay about 3.4 GB. No whole-clone archive is recommended: it would require additional space and complicate preservation of local imports and generated metadata.

## Verified identity and recoverability

The clone is detached at `5542e61610d20e591effbed9dec15fd10398e31d`. Its tracked status was clean before and after the audit. All **16,826 tracked files / 3,732,805,967 logical bytes** matched that commit's exact Git blob and executable mode; each streamed read also recorded SHA-256 and stable file metadata. There were no byte or mode mismatches. The audit took 6.51 seconds on CPU2 and did not run an engine or modify the clone.

[remote-and-object-storage.json](remote-and-object-storage.json) separately verifies the actual GitHub `refs/heads/game/yuga-native-production` at the exact commit. The clone's own `origin` is the local `/workspace/ANDOLAN`, so its `ls-remote` result alone is **not** evidence of publication. Its `.git/objects/info/alternates` also points to `/workspace/ANDOLAN/.git/objects`: retaining this clone's `.git` alone would not make it an independent object backup. Keep the canonical object store untouched. All 2,121 distinct proposed Git blobs are currently readable through that retained store; remote recovery remains possible from the verified public repository and commit.

| Proposed scope | Files | Logical bytes | Allocated file bytes |
| --- | ---: | ---: | ---: |
| `games/yuga-native/docs/evidence/` | 2,645 | 2,274,974,515 | 2,280,431,616 |
| `games/yuga-native/art/` | 87 | 832,171,556 | 832,339,968 |
| Total | 2,732 | 3,107,146,071 | 3,112,771,584 |

Selection requires an exact committed regular file, no symlink ancestor, one hard link, and size at least 262,144 bytes. The map records exact relative path, Git commit/blob, SHA-256, size, mode, device/inode/link count, timestamps, and recovery route. It is an individual-file allowlist; the two directory prefixes are **not** deletion targets. All directories and smaller files, including `.gdignore` and small authoring/receipt files, remain. Removing every tracked file under both prefixes would recover only another 276,787,200 allocated bytes while expanding removal to roughly 14,746 files; that wider scope is not proposed.

## Mandatory retention and current ownership hold

- Preserve all runtime assets, scripts, scenes, shaders, project/export configuration, notices, tools and tests outside the explicit map; preserve both Git directories and the canonical object store.
- Preserve every untracked or ignored clone file: [retained-untracked.json](retained-untracked.json) lists all 491 observed files, totaling 69,499,179 logical bytes. Nothing in that inventory overlaps the proposed map. This includes caches and generated metadata.
- The original UID-generation receipt contains 115 additions. All 115 still match their generation hashes; two are now committed runtime UIDs, leaving 113 untracked generated metadata files. Both categories remain protected.
- Preserve **all** r1 and r2 build, log, output, extraction, user, cache, export/package/qualification receipt, preparation, source-inventory and preserved-UID roots. [recovery-availability.json](recovery-availability.json) lists their observed top-level children. No recursive directory removal is proposed anywhere.
- W6 confirmed that the source clone remains a W1 capture dependency; W1 confirmed warm/cold attempts and final source audits have not released it. W6 subsequently confirmed a possible runtime-successor investigation also keeps cleanup held. Package evidence must retain its actual disposition; a source audit is not a substitute for runtime qualification.

The process observation found no visible file descriptor/map/cwd reference, but many processes were permission-inaccessible. This is **not** an idle-process proof, and does not override the explicit owner holds.

## Later execution conditions

1. Settle the exact package's qualification/disposition and any successor dependency. Obtain explicit W1 and W6 release of these historical clone files after final source/hash audits, followed by root approval of this exact map. A failed or stopped capture does not imply release.
2. Commit and remote-verify this recovery map and plan before deletion. Preserve the source, build and capture receipts elsewhere as their owners require.
3. Immediately recheck every mapped path against its recorded SHA-256/Git blob, size, mode, inode/device/link count and safe ancestors; confirm the expected detached HEAD and inspect current process references. Any mismatch, inaccessible unresolved owner, new dependency or changed path aborts that item. Do not broaden the map automatically.
4. Remove only approved individual files, leaving directories, unique files and all protected roots intact. No `git clean`, recursive prefix deletion, cache cleanup, Git pruning or whole-clone removal belongs to this plan.
5. Record actual removals and before/after filesystem capacity separately. The number above is a potential allocated-file total, not measured reclaimed space. Mark the source checkout as deliberately partial; package provenance checks or authoring reproduction may require the removed evidence/art and must restore it first.

## Exact recovery procedure

For each removed row, recover `git_blob` from the retained Git object database at the pinned commit using `git cat-file blob <git_blob>`. If those local objects are unavailable, use a separate verified checkout of `https://github.com/occult-kranti/ANDOLAN.git` containing the exact commit; do not overwrite this clone or its generated files. Confirm `git ls-tree` maps the recorded relative path to that blob and mode.

Write recovered bytes to a temporary sibling of the recorded destination after rejecting absolute/parent-traversal paths and symlink ancestors. Verify the recorded length and SHA-256, restore the recorded permission mode, then replace only a missing destination; never overwrite a changed or newly generated file. Verify the final Git blob and SHA-256. Directory structure is retained by this plan. Git does not preserve original timestamps, so exact content/mode recovery does not imply timestamp identity. No restore or removal command was executed during preparation.

Supporting files: [full tracked audit](tracked-audit.json), [summary](summary.json), [blob and generated-file availability](recovery-availability.json), [process observation](process-observation.json), and [read-only audit source](audit.py). The initial summary's `remote_branch_observation` is from the clone's local origin; use the explicit GitHub observation above for remote-backup proof.
