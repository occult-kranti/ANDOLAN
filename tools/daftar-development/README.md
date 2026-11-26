# Daftar development workspace for ANDOLAN / YUGA

This is a focused companion to Daftar's company, coding MoE and creative-tool
workflows. Open [andolan-yuga.code-workspace](andolan-yuga.code-workspace) in VS Code
to use the verified package checks and the existing Yuga build commands. Opening
the workspace starts no process, model download, paid service or authority change.

The source baseline is `game/yuga-hanuman-trial` at
`9e59880f31452ce0df8d326cd4f1291b700dc228`. Begin with the repository
[AGENTS.md](../../AGENTS.md) and [current entry point](../../docs/START_HERE.md).
The older default and distribution branches are distinct from this source.

## What this branch adds

- An original [Daftar Route Lab](../../games/yuga-native/art/daftar-route-lab/README.md)
  with editable Blender source, GLB, actual CPU preview and Blender reimport evidence.
- A read-only package check that verifies exact file and procedural-source hashes,
  reads the actual GLB vertex data, measures metre-scale bounds and checks all ten
  spawn positions against the plan-to-glTF axis conversion.
- A VS Code workspace with explicit process tasks for the lab, authored map audits,
  Rust authority tests/build and the retained Godot comparison import.
- A source and engine [project profile](project.json) linking this checkout to
  the Daftar company setup. It is metadata, not evidence of a running model or team.

The original authored maps and runtime asset paths remain in place. The new art
package lives under `art/`; the project's existing authoring/import boundary still
applies. An imported engine scene, navigation mesh or gameplay level is not created
by the presence of this package.

## Use the package checks

From the repository root:

```sh
node tools/daftar-development/check.mjs
node --test tools/daftar-development/check.test.mjs
```

The delivered GLB contains 73 mesh nodes and 11,602 position samples. Its measured
glTF bounds are `[-24, -0.4, -28]` to `[24, 3.37, 28]` metres, with +X east, +Y up
and −Z north. The check accepts this deliberately small, flat-scene export; it is
not a general glTF validator. It rejects external buffers, out-of-bounds position
accessors, wrong units, moved/missing spawns and stale artifact evidence. It does
not launch an engine or infer gameplay behavior.

To perform a new actual Blender reopen/reimport check:

```sh
blender --background --factory-startup --disable-autoexec --threads 2 \
  --python-exit-code 1 \
  --python games/yuga-native/art/daftar-route-lab/verify_route_lab.py
```

That command writes the lab's `geometry-acceptance.json` after checking the current
package. The procedural build command in the art README overwrites its generated
files; use its `--output-dir` option for a new candidate. Queue rendering/import
work and retain meaningful failed runs as the repository art workflow requires.

## Existing game tasks

Use **Tasks: Run Task** in the included workspace. Each task uses an explicit
program and argument array, has no automatic folder-open trigger, and retains
the existing source command.

| Task | Required source/tool boundary |
| --- | --- |
| Verify Route Lab package / test its checks | Node; included original package |
| Reimport Route Lab in Blender | Blender; package source and export beside the verifier |
| Verify authored map routes | Python; four Ember Rite JSON plans and current `measurements.md` |
| Verify/test authored map balance | Python; atlas source plus `games/yuga-rust/src/ritual.rs` and `assets/vanara-sena.json` |
| Test Rust authority | Cargo; full `games/yuga-rust` source and lockfile |
| Build Rust browser package | Existing `build_web.py`, installed locked dependencies and the documented Rust/WASM toolchain |
| Import Godot comparison assets | Installed matching Godot and the complete retained native project |

A sparse source review does not contain the full binary asset set. Expand the
required paths before a full game build or import. The existing
[Rust README](../../games/yuga-rust/README.md) and
[native build handbook](../../games/yuga-native/docs/BUILD_HANDBOOK.md) remain the
toolchain authorities. This branch does not claim those full game builds were
rerun merely because their editor task entries exist.

## Daftar company and coding model

The companion
[ANDOLAN / YUGA company kit](https://github.com/occult-kranti/engineering-intelligence-atlas/tree/feat/donna-moe-creative-studio-20261125/projects/andolan-yuga-development)
uses Daftar's native company-kit schema and additive command boundary. It reuses
the existing exact repository-bound company and six bootstrap office specialists,
adds four focused specialists, and binds source-specific role contracts and seven
development gates. A real setup receipt contains the actual employee IDs; a kit
file does not mean the owner's live workspace was changed.

The first reviewed coding model is
[`qwen3-coder:30b-a3b-q4_K_M`](https://ollama.com/library/qwen3-coder:30b-a3b-q4_K_M),
with 30.5B total / 3.3B active parameters. Use the exact tag, a verified installed
digest, Daftar's 8,192-token context profile and one inference request at a time.
The approximately 19 GB download is not a measured VRAM requirement. Start with
one bounded patch and independent tests. Model routing, staff roles and an actual
MoE model are separate concepts; this workflow does not train new weights.

The kit does not enable workers, install software, rent hardware, grant broad
authority, alter budgets or send external messages. Select and run actual work
through the current connected Daftar runtime and inspect its native receipts.

## Unreal experiment boundary

The inspected branch has Rust/WASM and PlayCanvas gameplay plus the retained
Godot comparison. It has no existing Unreal project. Keep an Unreal experiment
separate and select a real installed engine and `.uproject` before using Daftar's
Unreal validation/import workflow.

Import the exact lab GLB into a new sandbox scene, preserve node transforms and
verify approximately 4,800 × 5,600 centimetres of ground. Create collision and
navigation deliberately; decorative route marks, the objective ring and spawn
mannequins are not automatic collision or gameplay objects. Capture actual editor
and render evidence before marking Unreal acceptance. The portable geometry and
CPU preview do not establish that this step has run.

The current authored-map next gate remains the documented isolated Mandala slice:
ordinary dry paths, selected solids, legal interaction, interruption/reset/side
swap and authoritative event ordering, with folds closed initially. Retain the
two-rendered-client and human playtest gates.

## Validation record

[validation.json](validation.json) records commands actually run for this scoped
integration. The five package tests include negative cases for corruption,
external buffers, wrong scale, moved/missing spawns, stale evidence and path escape.
The authored route and balance checks retain their own scope. Full game execution,
engine collision/navigation, GPU profiling, Unreal import/render and live model
inference remain separate work.
