# Successor package preparation — source only

Prepared and reviewed 18 October 2026. No production artifact checkout, import, export, package assembly, cleanup or publication has been run. The current canonical source is still dirty `d199f607`; it is not the successor package source.

Recovered `prepare-package-snapshot.py` and `run-package-phase.py` are complete. The first defaults to a plan. Actual preparation requires a full 40-character HEAD equal to the current remote branch, exact tracked blob/mode/index closure, no sparse/assumed-unchanged entries, no untracked native runtime inputs, exact approved r4 nonruntime UID exclusions, fresh destination and enough capacity. It creates an artifact-only shared-object Git clone with complete tracked source. Mutable native text/config/scripts/scenes/shaders/notices/tools/tests and all tracked UID/import sidecars are private copies. Frozen raw asset inputs and historical evidence may share inodes. Every private-copy/hardlink decision and all cache files are audited; the native cache is always private. No shared inode is chmodded. The canonical source and linked frozen evidence must remain unchanged until after package auditing.

The phase runner keeps every existing source, UID, PCK, font, contract, archive and engine guard in `package-native.py`. It explicitly selects official exporter `f64d4ed1` and patched Linux runtime `e69af4f6`, `pipeline-low-priority`, with the exact committed provenance. Export/package use CPU 0,1 only after W1 releases the serialized lane, a 300-second process-group bound, preserved logs/failure receipts and a continuously checked declared reserve. Canonical tracked bytes/index/cache and artifact source/index/inodes are compared before and after each phase. Generated nontracked UID/import metadata is recorded; unexpected visible source files still fail clean status. There is no new exclusion or broad ignore.

`check-snapshot-guards.py` passed **23/23** synthetic checks, including corruption, mutable shared inode, symlink, sparse/assumed index, missing index member, source freeze, unsafe path, and insufficient declared reserve cases. It creates only a small retained synthetic fixture under scratch, not an application artifact checkout. `snapshot-guard-checks.json` pins both runner source hashes. AST parsing passed for all three scripts. The full application snapshot/export/package remain unexecuted.

Current planning recomputation for the unchanged HEAD: 19,918 tracked files; 1,789 private files / 22,065,152 rounded bytes; private cache 70,934,528 rounded bytes. Observed free space was 1,396,989,952 bytes. Planned peak including the approved **128 MiB export reserve** was 1,067,971,840 bytes, leaving 329,018,112 bytes of additional allowance. Recompute at the final freeze; these are not acceptance measurements. A 500 MiB render reserve remains separate. No renderer may run concurrently. Only after successful ZIP/member/PCK/source/manifest audits may root approve a fresh exact map for expanded successor duplicates. No old package/cache cleanup is authorized by these runners.

Root authorized and reviewed generation of two missing test UID sidecars through official Godot `ResourceUID.create_id()` / `id_to_text()` in a private empty scratch directory. Both new IDs were absent from 248 existing live script/shader/test/tool UID values; the existing runtime UID preflight passed all 75 runtime scripts. `test-uid-generation.json` pins both paths and hashes. Root owns adding these source files to the final commit; no UID exclusions were added.

After W2/W4 release, root checks, final accepted source commit/push, runner review and W1 lane release, the literal commands below are ready. `rev-parse` supplies the full exact HEAD and the script independently checks remote equality. A new final source must use a fresh artifact name and fresh report names.

```sh
cd /workspace/ANDOLAN
YUGA_SUCCESSOR_COMMIT=$(git rev-parse HEAD)
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/prepare-package-snapshot.py --commit "$YUGA_SUCCESSOR_COMMIT" --artifact-name package-successor-r1 --reserve-mib 128 --report /workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-plan.json
```

Review that plan, then root's explicit materialization instruction is the remaining scheduling gate:

```sh
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/prepare-package-snapshot.py --commit "$YUGA_SUCCESSOR_COMMIT" --artifact-name package-successor-r1 --reserve-mib 128 --report /workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-preparation.json --materialize
YUGA_SUCCESSOR_PREPARATION_SHA=$(python3 -c 'import hashlib; from pathlib import Path; print(hashlib.sha256(Path("/workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-preparation.json").read_bytes()).hexdigest())')
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/run-package-phase.py export --preparation /workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-preparation.json --preparation-sha256 "$YUGA_SUCCESSOR_PREPARATION_SHA"
```

The phase command above prints the exact export invocation without running it. With the lane released and root scheduling it:

```sh
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/run-package-phase.py export --preparation /workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-preparation.json --preparation-sha256 "$YUGA_SUCCESSOR_PREPARATION_SHA" --execute
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/run-package-phase.py package --preparation /workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-preparation.json --preparation-sha256 "$YUGA_SUCCESSOR_PREPARATION_SHA"
```

After reviewing that package-only plan and successful export receipt:

```sh
python3 games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/run-package-phase.py package --preparation /workspace/scratch/yuga-continuation-W6-r1/package-successor-r1-preparation.json --preparation-sha256 "$YUGA_SUCCESSOR_PREPARATION_SHA" --execute
```

No command here extracts or qualifies actual gameplay. Publication still requires exact successor archive audit, extracted sibling-engine/PCK warm execution, independent fresh-user cold execution, actual-original review and byte/receipt identity checks. Public `96d5b9cd` remains separately qualified until that finishes.

The old `published/transport-r2` mechanism is a temporary orphan transport with a private index and streaming Git blobs, not the regular native release workflow. It is pinned to old source `96d5b9cd`, branch `transport/yuga-desktop-finish-2026-10-18-r2`, and draft release ID `416367666` (now public). Its uploader rejects any non-draft target and cannot be reused verbatim. Root owns any narrow successor transport source/branch/draft/asset/qualification pins and its independent source review; no workflow, API mutation or publication was performed here.
