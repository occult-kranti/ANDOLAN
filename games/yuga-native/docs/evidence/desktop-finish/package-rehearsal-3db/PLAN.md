# Exact 3db package rehearsal — prepared, not executed

Source: `3db9158ff1be3806a406d6b561e9523188428590`. This is a bounded export/archive rehearsal proposal, not a release or a package qualification. The lead must choose the source/art scope and serialized engine slot before execution. No worktree, import, export, archive, or publication was performed for this plan.

[inputs.json](inputs.json) records the exact checkpoint tool/config hashes and currently available official Linux and Windows engine payloads. The package/export tools match the checkpoint. The canonical worktree now contains two later runtime changes: the loading error-copy correction and promoted paving include. An export of that worktree cannot be described as exact `3db`. Existing render children, user saves, approved packages and source evidence remain untouched.

## Source preparation and stop conditions

1. After lead authorization, create a fresh isolated checkout of the entire repository at the exact commit. Preserve `ANDOLAN/games/yuga-native` nesting: the packager reads sibling browser model/rule files, historical contract fixtures, notices and authoring sources. Do not copy only the native scenes/scripts or overlay current working files.
2. Record HEAD, tracked/untracked status, runtime source inventory and every selected engine/tool hash. Use isolated XDG locations. The normal official Linux engine is `f64d4ed1…`; the successful public-template renderer used for screen diagnostics is a separate binary and is not selected here.
3. Coordinate one private import if the exact checkout lacks compatible imports. Record raw assets, descriptors and generated cache payloads before/after. New `.uid` sidecars or changed descriptors are explicit source changes: retain the failed/prepared result and request a source-bound disposition; do not silently label generated additions as the original Git tree. No canonical cache is written.
4. Run the existing `package-native.py --export-only` once with a fresh build directory, then inspect its actual reports and logs. The fixed 240-second per-PCK export bound remains unchanged. Do not treat a process exit alone as success.
5. Only after export qualification, run `--package-only` against those same outputs and source. Keep all manifests, source inventories, PCKs, raw logs, expanded outputs and ZIPs. A failed check remains evidence; do not modify source in place and overwrite it.

Proposed commands, **not executed** (the lead chooses the fresh paths and engine slot):

```bash
# First create the approved exact checkout; do not run in the shared working tree.
git -C /workspace/ANDOLAN worktree add --detach \
  /workspace/scratch/package-rehearsal-3db-r1/ANDOLAN \
  3db9158ff1be3806a406d6b561e9523188428590

# After isolated import/source disposition and lane authorization:
cd /workspace/scratch/package-rehearsal-3db-r1/ANDOLAN
export XDG_DATA_HOME=/workspace/scratch/package-rehearsal-3db-r1/user/data
export XDG_CONFIG_HOME=/workspace/scratch/package-rehearsal-3db-r1/user/config
export XDG_CACHE_HOME=/workspace/scratch/package-rehearsal-3db-r1/user/cache
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1

taskset -c 0,1 python3 games/yuga-native/tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir /workspace/scratch/package-rehearsal-3db-r1/build \
  --export-only

# Separate review boundary: same source/engines, fresh package outputs in that build.
taskset -c 0,1 python3 games/yuga-native/tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir /workspace/scratch/package-rehearsal-3db-r1/build \
  --package-only
```

Capture each command's complete stdout/stderr and exit code in fresh files; commands above do not imply the initial source/import gates were executed. If verified engine files are unavailable, the existing `release-native.py install-engines --destination <fresh-directory>` owns verified acquisition. Do not install or download speculatively.

## Existing gates to preserve

The packager proves current versioned contract source closure, staged world consistency, active hero/schema-5 provenance and exact historical parent bindings, world/film/audio notices, both exported PCK member hashes and remaps, and runtime/provenance/contract stability across export. Its actual same-export font probe compares decoded `FontFile.data` with the three raw bundled TTFs; historical imported-font hashes are not substituted. It then rechecks those dependencies during packaging, validates the Windows engine against the adjacent provenance record, and verifies exact ZIP membership, CRCs and member payload hashes.

The required first-load closure is boot scene, boot controller, scene transition, loading presentation, launch shell and shared theme. Current graphics requirements include infantry art, environment finish, ability glyphs, hero finish, masonry shader, the G1/S1 manifests, and the promoted roughness textures/remaps. Optional upper-hair layers, fletching, crown, shoulder, hair and roof review candidates remain inactive and receive no activation/acceptance claim from this rehearsal. Historical notice dependencies remain required.

Inspect `native-contracts-export.json`, `font-bindings-export.json`, `native-export-manifest.json`, `export-*.log`, both PCKs, and then the corresponding package contract/font checks plus `native-package-manifest.json` and both ZIPs. Reject unexpected warnings/errors, missing members, altered source/contract/provenance, self-hash/ancestry failures or mismatched font payloads rather than weakening existing tests. No known package blocker has been established by this read-only plan; gates have not been run locally for it.

## Qualification boundary

Archive/PCK qualification is separate from execution. Any future extracted Linux input/capture must use the exact new binary/PCK, isolated state, explicit source identity and native Quit; prior journey screenshots are not images of a new package. Windows remains unexecuted until separately tested. `release-native.py validate-evidence`, `stage`, `verify` and `publish` belong to a later release decision, not this rehearsal; no publication is requested or authorized here.

The exact `3db` Actions run is [39107059307](https://github.com/occult-kranti/ANDOLAN/actions/runs/39107059307). Its final result must be recorded independently and must not be relabeled to the later copy or paving changes.
