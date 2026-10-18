# Combined desktop package successor — prepared, unexecuted

This plan applies to the **future exact integration commit**, after the lead accepts the checkpoint allowlist. It does not export the shared working tree or relabel checkpoint `3db9158f` or cleanup-only `8acd7b35`. No clone, import, export or package command below has run.

The intended active deltas are the reviewed three-LOD smooth crown followed by the accepted selected sash UV correction in a flat schema6 sequence, title lighting, distant paving colour, loading error-copy deduplication the accepted bounded landing-support correction, and the map heading/precision correction using the actual visual-facing vector. The optional upper-hair helper and guide retain their original checkpoint bytes; their offline source-compatibility proof does not activate the helper. Hair and shoulder candidates remain excluded. The lead accepted the bounded roof recipe and overview composition. Their combined caller/helper, original notice, generated UID and focused source receipt must be included in the final source commit. The landing acceptance retains the recorded 26/27 strict-comparison limit and does not establish general continuous smoothness.

## Storage and source preparation

[storage-estimate.json](storage-estimate.json) records the final preparation measurements. HEAD's tracked tree is 3,261,160,588 bytes; the selected integration adds approximately 468,524,460 bytes, giving a projected full checkout of 3,729,685,048 bytes. The canonical native `.godot` directory is about 69.5 MB. A local clone with a shared, read-only Git object store avoids a second object database while keeping export sources and writable caches independent. Allow 1.25 GiB for cache, two PCKs, expanded packages, ZIPs and logs, plus a 1 GiB free reserve and 1 MiB metadata margin: approximately 5.72 GiB total. Current `/tmp` free space is 5.61 GiB. The lead's separately reviewed cleanup map plans to recover 728,309,760 allocated bytes from released old source copies only after the checkpoint is pushed. No such deletion is performed by this W6 plan. Verify its execution receipt and remeasure the exact committed tree and available space before cloning.

Use a fresh `/tmp/yuga-desktop-integrated-package-r1` root and preserve the full `ANDOLAN/games/yuga-native` nesting. The packager reads sibling browser assets/rules and historical authoring/contract files. A lean screen snapshot is insufficient. The shared Git object store must remain available throughout preparation; no Git cleanup is part of this plan.

The lead supplies the full approved commit as `integration_commit`. The following uses the already verified official engines; the diagnostic public-template renderer is not substituted. This is one qualified successor attempt after the checkpoint, not a separate export rehearsal of unchanged source:

```bash
set -euo pipefail
# Set this to the exact newly committed and reviewed 40-character source ID.
integration_commit=REPLACE_WITH_APPROVED_FULL_COMMIT
integration_root=/tmp/yuga-desktop-integrated-package-r1
test "${#integration_commit}" -eq 40
git -C /workspace/ANDOLAN cat-file -e "$integration_commit^{commit}"
test ! -e "$integration_root"
mkdir "$integration_root"
git clone --shared --no-checkout /workspace/ANDOLAN "$integration_root/ANDOLAN"
git -C "$integration_root/ANDOLAN" checkout --detach "$integration_commit"
test "$(git -C "$integration_root/ANDOLAN" rev-parse HEAD)" = "$integration_commit"
git -C "$integration_root/ANDOLAN" status --porcelain=v1 > "$integration_root/source-initial-status.txt"
test ! -s "$integration_root/source-initial-status.txt"
mkdir "$integration_root/build" "$integration_root/logs"
```

Before any engine command, record the full tracked/source inventory, official engine hashes, import descriptor/cache mapping and free space. An independent byte-copy of the exact qualified cache may be used only after its raw/descriptors are proved to match this commit and all copied payloads are hashed. Do not hardlink a writable cache or infer freshness from filenames. Otherwise, use one separately authorized private import and retain its complete source/cache delta. No canonical cache write is required.

The lead approved deliberate inclusion of exactly two existing runtime sidecars, `scripts/rama_ability_glyph.gd.uid` and `scripts/rama_upper_hair_layers.gd.uid`, after the [syntax/uniqueness audit](runtime-uid-audit.json). This does not activate upper hair. Unrelated generated test/tool UIDs remain excluded. The roof-script UID is separately recorded by W4’s isolated minimal-project generation and included by its exact digest. If preparation/export creates any other absent runtime sidecars or changes descriptors, stop with the source-change receipt; the lead must disposition a source-bound successor. The existing export guard remains unchanged.

## Existing export and package commands

After the source/cache gate and a serialized engine grant, run once with fresh logs. Keep the packager's existing 240-second per-PCK limit and 60-second font-probe limit.

```bash
cd "$integration_root/ANDOLAN"
export XDG_DATA_HOME="$integration_root/user/data"
export XDG_CONFIG_HOME="$integration_root/user/config"
export XDG_CACHE_HOME="$integration_root/user/cache"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1

taskset -c 0,1 python3 games/yuga-native/tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir "$integration_root/build" --export-only \
  > "$integration_root/logs/export-driver.log" 2>&1
```

Retain the actual exit code. Inspect both PCKs, `native-export-manifest.json`, native-contract and same-export FontFile proofs, all export logs, source/provenance stability and Git status before continuing. The new schema6 gate must validate the final promoted trio, immutable crown intermediates and exact old notice chain. W6's source/package fixture results do not substitute for these export gates.

```bash
# Separate review boundary: use the same unchanged source, cache, engines and build.
taskset -c 0,1 python3 games/yuga-native/tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir "$integration_root/build" --package-only \
  > "$integration_root/logs/package-driver.log" 2>&1
```

Preserve both PCKs, expanded folders, ZIPs, manifests and logs. Verify actual member hashes/CRCs, exact font remaps, the newly copied parent/crown attribution companions and unchanged source/contract bindings. Run no repeat into the same build directory after a failure; the current packager replaces expanded staging directories.

## Bundled engine and actual qualification

The existing `--linux-engine` argument supplies the exporter, font probe and bundled Linux executable. Keep the official `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3` engine for all three. The recent native visual captures used the separate unmodified public-template `dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f` executable after the installed engine's cold first-draw lock. Those captures do not establish execution of the official binary in the new package. No exporter/runtime parameter split or silent binary substitution is part of this plan.

After archive validation, extract the exact new Linux ZIP once into a fresh directory and execute its own bundled `godot`/launcher. First run with a copied, hash-recorded Godot/Mesa cache seed, using the existing native input/capture tools and isolated state. Record the actual binary, PCK, source, cache seed, first visible frame, route completion and native Quit. The native route must include a rotated hero in ordinary view and overview: record the actual visual-facing vector and atlas heading, and verify their agreement through overview entry/exit. The earlier always-north fixture does not establish this behavior. Then run a separate cold qualification with fresh XDG state and no copied shader caches, using the already justified 600-second first-draw allowance and progress diagnostics. Keep these warm and cold claims separate; neither is a physical-GPU benchmark.

If the official executable locks again, preserve the incomplete capture, process diagnostics and source/cache identities. Report package execution as blocked, while keeping the source checkpoint publishable. The next decision can explicitly introduce and test a separate runtime parameter using the independently retained public-template provenance; it must not rewrite this attempt or call earlier public-template captures official-package acceptance. No new parameter is implemented preemptively.

A qualified archive remains separate from execution. Native Windows, physical-GPU performance and publication remain unrun/unapproved by this plan. Prior journey/crown/light images retain their exact earlier source and engine scope.
