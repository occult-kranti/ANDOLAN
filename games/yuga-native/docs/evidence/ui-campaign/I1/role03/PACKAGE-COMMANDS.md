# I3 package execution preparation

Prepared commands only. Wait for root's final source commit and the I2 sequence disposition before execution. The current public release remains `yuga-rama-hero-2026-10-17`; none of these commands publishes it or a successor.

`tools/package-native.py` is the export/package entry point. `tools/release-native.py` currently admits historical Confluence/Traversal tag families and cannot stage a Rama/UI tag without a separate current release contract. Do not borrow an old tag or capture to pass its gates.

## Source requirements

Use the complete `/workspace/ANDOLAN` checkout, with the accepted runtime, assets/import descriptors, strict package support, 66 authoring-source ancestry and notices committed at the exact requested HEAD. Do not package the trimmed capture freeze. The final I1 freeze is `/tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native`, manifest `9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088`; if I2 repairs change runtime, a successor freeze and explicit reconciliation are required.

Before export, compare every `source_state()` runtime path and hash to the final freeze and committed Git blob; verify required raw fonts, descriptors, same-import payloads, notices and full hero ancestry. Preserve any meaningful failed report. Working documentation from other owners is not an excuse to accept uncommitted runtime or provenance inputs.

The two validated official engines already exist. Reuse them and the verified current import cache. Do not download engines, duplicate a full project, rebuild/re-export hero assets or rerun imports unless a concrete mismatch requires it.

## Serialized export and archive commands

From `games/yuga-native`, after the exact commit check and explicit lane release, choose one fresh build directory. Substitute root's actual commit for the placeholder before running:

```sh
YUGA_PACKAGE_COMMIT=ROOT_FINAL_COMMIT
YUGA_PACKAGE_BUILD=/workspace/scratch/ui-campaign/I3/package-r1
test "$(git rev-parse HEAD)" = "$YUGA_PACKAGE_COMMIT"
test ! -e "$YUGA_PACKAGE_BUILD"
mkdir -p "$YUGA_PACKAGE_BUILD"
taskset -c 0,1 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  XDG_DATA_HOME="$YUGA_PACKAGE_BUILD/xdg/data" \
  XDG_CONFIG_HOME="$YUGA_PACKAGE_BUILD/xdg/config" \
  XDG_CACHE_HOME="$YUGA_PACKAGE_BUILD/xdg/cache" \
  python tools/package-native.py --export-only \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir "$YUGA_PACKAGE_BUILD"
```

Review both export logs and `native-export-manifest.json`: requested Git HEAD, unchanged runtime signature, 66-source hero ancestry, same-export FontFile data binding, three exact packed fonts, all five direct/remapped first-load dependencies, directory/payload integrity and exact engine identity. Then package those same exports once:

```sh
taskset -c 0,1 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  XDG_DATA_HOME="$YUGA_PACKAGE_BUILD/xdg/data" \
  XDG_CONFIG_HOME="$YUGA_PACKAGE_BUILD/xdg/config" \
  XDG_CACHE_HOME="$YUGA_PACKAGE_BUILD/xdg/cache" \
  python tools/package-native.py --package-only \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir "$YUGA_PACKAGE_BUILD"
```

The tool verifies both ZIP entry sets, CRCs and every payload SHA, engine/notice bytes, launcher and current **Watch duel** instructions. Record archive, aggregate/export manifests and per-platform manifest hashes. Windows remains **archive validated, unexecuted**.

## Exact Linux qualification

Extract the exact new Linux ZIP into one fresh directory, verify extraction against `PACKAGE-MANIFEST.json`, and use that extracted `launch.sh` with isolated XDG state. Coordinate the actual desktop/input owner and display lane. Qualify first load, both playable modes, five actions, Help/guide, pause/preferences and saved remaps, return, resize and recovery paths; bind inputs, logs and actual pixels to the archive SHA. Historical source captures and structural PCK checks do not replace this run.

Disk available at preparation was about 3.5 GB. Keep one pair of exports/archives and one Linux extraction; reuse the existing engines and original project. The previous historical PCK was about 25 MB, but it does not predict the new pack size. Recheck free space after actual export before staging/extraction; retain unique evidence and use root's duplicate-only cleanup policy if necessary.

No engine export, archive generation, extracted package execution or publication has run as part of this preparation.
