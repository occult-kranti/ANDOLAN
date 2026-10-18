# Exact successor restoration and r4 package procedure

Prepared only. No clone writes, restore, exclusion edit, checkout, export, packaging, cleanup, or engine invocation has occurred. The target commit is deliberately unset until the lead confirms its pushed SHA. Existing r1/r2/r3 outputs and sealed warm/cold evidence remain historical.

## Entry gates

Use the existing owned checkout `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN`; do not clone again or copy canonical working files. The lead must first confirm the new source commit and remote ref, execute only the separately published cleanup maps, freeze runtime, and release CPU0,1 after W1's current take. Resolve the exact commit object through the existing Git alternate; no canonical Git mutation or garbage collection.

Inventory the owned checkout before any write: HEAD must still be f8dec5f; tracked differences must be exactly the 2,732 mapped deletions, with no other staged/tracked changes. Verify the map SHA in `recipe.json`, each path's f8 Git blob/mode against its map row, all 115 retained generated metadata hashes, and the existing exact non-runtime exclusion file against r3. Check accessible live process cwd/exe/fd/maps/arguments plus owner releases. Refuse unexpected files, symlink ancestors, or source holders.

Capacity must include **missing-file restoration plus the exact target Git tree delta** and reserve. The earlier restoration-only floor is insufficient: d1 alone adds about 880 MB of historical art, and this checkpoint adds roughly 85 MB of evidence. Measure the final target, round each newly materialized blob to the filesystem allocation size, avoid double-counting files already restored/present, and check `/tmp` independently from `/workspace`. The new build lives on `/workspace`; this does not eliminate new source bytes on `/tmp`. Retain published cleanup execution receipts and actual free-space observations. Stop on a shortfall; do not widen cleanup.

## Restore, advance, and freeze

1. Restore only each missing map destination using its exact local Git blob. Stream `git cat-file blob <recorded-blob>` into a temporary sibling, verify recorded byte count and SHA-256, and install a regular file with its recorded disk mode and matching Git executable bit. Reject an existing destination or symlink ancestor. Do not restore from mutable canonical files or use links/skip-worktree/ignore to conceal missing source.
2. Verify all restored hashes and executable modes; require the full old tracked tree clean. Record restoration results separately from original cleanup receipts.
3. Advance only this owned checkout with `git checkout --detach <exact remotely verified successor>`. Recheck full tracked bytes/modes against that Git tree. Preserve the original 113 exclusion lines and all prior generated metadata. Root approved one additional exact line: `/games/yuga-native/tests/ui_focus_recovery_cases.gd.uid`. Archive before/after exclusion text and hash; no wildcard, runtime path, canonical ignore, or manually invented UID. If export generates it, preserve and hash its exact bytes.
4. Audit the runtime delta against r3/f8: only the accepted guide and Controls focus scripts listed in `recipe.json` should differ. The new source checkpoint also contains package/test/docs evidence, which must not be mislabeled as runtime changes. Reject any extra runtime delta pending disposition.
5. Create the fresh r4 output directory only if absent. Adapt the retained [r3 preparation driver](../../package-export-r3/W6/preparation-driver.py) to the confirmed target and new output root. Capture full tracked-source, runtime, cache, generated-metadata and protected prior-output inventories. Account explicitly for files removed by the separate published duplicate maps; never claim those deleted duplicates remained present. Retain all ZIPs, remaining Linux raw PCKs, logs/manifests/SUMS and source/cache data.

## Export, then package — later execution only

Reuse the retained [phase wrapper](../../package-export-r3/W6/run-phase.py), with a fresh receipt/log path, target commit, output root and the exact runtime arguments below. Keep CPU0,1, the existing 300-second per-phase bound, fresh isolated XDG directories, and OMP/BLAS thread limits. Preserve failure logs and partial outputs; do not overwrite or silently retry them.

From the owned checkout's `games/yuga-native` directory, the two commands differ only in the final phase flag:

```sh
python tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --linux-runtime /workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority \
  --linux-runtime-variant pipeline-low-priority \
  --linux-runtime-provenance docs/evidence/desktop-finish/G0/template-priority-build-r1/finished-build-verification.json \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir /workspace/scratch/yuga-desktop-integrated-package-r4/build \
  --export-only
```

First inspect the export's exact source/engine/font/native-contract guards and log. Only after successful disposition, execute the same arguments with `--package-only`. Do not rerun broad unchanged source suites. No export or package phase is currently authorized by this procedure alone.

## Exact qualification and handoff

Adapt the retained [r3 qualification script](../../package-export-r3/W6/qualify.py), keeping complete before/after tracked/runtime/metadata checks and ZIP membership/CRC/payload verification. Replace f8/dce identity assumptions explicitly: target is the new pushed source; official exporter is f64; bundled Linux runtime is e69, kind `patched-public-source-template-debug`, variant `pipeline-low-priority-v1`, one patch. Verify all eleven source/build/license evidence records through their full mapped ZIP paths, including both same-basename build histories. Check each manifest, runtime/PCK byte hash, Linux executable mode and patched START-HERE/NOTICE; Windows remains independently described. Derive member counts from actual manifests rather than reusing r3's count.

Record cache deltas and any newly generated exact focus-test UID. Preserve clean Git/source guards. Produce SHA256SUMS.txt over the two ZIPs and two manifests, then send W1 the five-asset hashes, exact source/build/PCK/runtime identity and explicit heavy-lane release. Every package still says `not_executed_by_packager`.

W1 owns a separate W1-r4 preparation successor. Keep its warm25/cold10 plans, observer and runner unchanged where the interface is unchanged, but bind the new source and artifact hashes, actual bundled e69 runtime and complete patched provenance. Pin both accepted focus-script bodies through the export manifest; component focus adversaries remain separately attributed. Remove diagnostic-override semantics: the new ZIP's runtime itself must execute. Warm and independently fresh cold qualification apply to that new extracted artifact; the f8 diagnostic successes do not substitute for them. The existing f8 release transport stays held and must be regenerated for new assets/source after acceptance.
