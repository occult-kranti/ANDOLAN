# Daftar development workspace for ANDOLAN / YUGA

This is a focused companion to Daftar's company, coding MoE and creative-tool
workflows. Open [andolan-yuga.code-workspace](andolan-yuga.code-workspace) in VS Code
to use the verified package checks and the existing Yuga build commands. Opening
the workspace starts no process, model download, paid service or authority change.

The source baseline is `game/yuga-hanuman-trial` at
`a35493d67cf5111d7da2ff9eea6c58ed3499aeca`. Begin with the repository
[AGENTS.md](../../AGENTS.md) and [current entry point](../../docs/START_HERE.md).
The older default and distribution branches are distinct from this source.

## What this branch adds

- An original [Daftar Route Lab](../../games/yuga-native/art/daftar-route-lab/README.md)
  with editable Blender source, GLB, actual CPU preview and Blender reimport evidence.
- A read-only package check that verifies exact file and procedural-source hashes,
  reads the actual GLB vertex data, measures metre-scale bounds and checks all ten
  spawn positions against the plan-to-glTF axis conversion.
- A VS Code workspace with twelve explicit process tasks for an isolated Python
  environment, the lab, authored map audits, Rust authority tests/build and the
  retained Godot comparison import.
- A source and engine [project profile](project.json) linking this checkout to
  the Daftar company setup. It is metadata, not evidence of a running model or team.

The original authored maps and runtime asset paths remain in place. The new art
package lives under `art/`; the project's existing authoring/import boundary still
applies. An imported engine scene, navigation mesh or gameplay level is not created
by the presence of this package.

## Current authored work

[Monsoon Exchange](../../games/yuga-native/art/monsoon-exchange/README.md) is an authored district and browser walk, not this Route Lab or a server-playable map. Start with the survey and Blender/GLB receipts before engine collision and ten-client commissioning.

Run **Yuga: Test Ember Rite solo movement and audio** in VS Code to check the exact solo drill. It runs neither a browser nor a live match. The [audio QA](../../games/yuga-native/docs/design/ember-rite-5v5/audio/qa.md) separates listener behavior in the drill from the remaining authoritative, ten-seat, and physical listening checks.

Team revision `yuga-a35493d-20261126` adds a gameplay audio owner and an
animation/performance owner. The first coordinates accepted listener receipts,
captions, stale events and reconnect clocks with Rust authority. The second binds
cast, takeoff, contact and recovery witnesses to actual motion/audio markers and
rendered-client timings. The map owner commissions Monsoon's thirteen rooms,
eighteen connections, ten pads, seven thresholds and two ritual sites. Independent
QA owns the ten-seat/two-rendered-client gate and retains separate human
listening, game-feel and physical-GPU requirements.

## Install and use the Python venv

Run **Yuga: Create isolated Python venv** once. Enter the absolute path of a trusted
installed Python 3.10+ interpreter with `venv` and `ensurepip`. The task creates
`tools/daftar-development/.venv/`, installs Python's bundled pip without a package
index, and prints the exact interpreter to use. If the selected interpreter
fails, the helper reports that failure; it does not choose another interpreter.

Equivalent commands from the repository root:

```sh
node tools/daftar-development/python-workspace.mjs create --python /absolute/path/to/python3
node tools/daftar-development/python-workspace.mjs check
node tools/daftar-development/python-workspace.mjs routes
node tools/daftar-development/python-workspace.mjs balance
node tools/daftar-development/python-workspace.mjs test-balance
```

Use `--venv /absolute/environment/path` on every command when selecting a
different environment. The helper never overwrites an existing non-venv directory.
It requires exactly one `include-system-site-packages = false` setting and verifies
the real interpreter prefix, disabled user site, excluded base packages and its
own pip. An existing environment with global packages enabled is rejected.
On Windows the base interpreter root can be a normal standard-library/DLL search
path: the check allows that exact root while still excluding the actual
`Lib/site-packages` directories for both base prefixes. Failed inspections name
the specific failed checks. The directory distinction follows
[CPython 3.12's site implementation](https://github.com/python/cpython/blob/v3.12.10/Lib/site.py).

The four Python editor tasks call this helper and its verified interpreter with
isolated mode and an explicit `-X utf8` flag. The flag keeps Unicode report
comparisons and piped diagnostics consistent on Windows even though isolated
mode ignores `PYTHONUTF8`. The helper also sets its own `PYTHONUTF8=1` for reviewed
build scripts' Python children that do not inherit interpreter flags. Only the
selected script's source directory is added for existing
sibling imports such as `audit` and `ritual_rules`. Terminal activation is
unnecessary. If using VS Code's Python extension, select the interpreter printed
by the check: `.venv/bin/python` on POSIX or `.venv/Scripts/python.exe` on Windows.
Do not commit the local venv; the checked-in helper recreates it.

These Python checks use the standard library. Python isolation is not a sandbox
for untrusted source. VS Code, Node, Cargo and the engines remain their own
programs; Blender uses its embedded Python for authoring. The explicit browser
build keeps its existing Cargo/Node/toolchain prerequisites and may fetch those
tools' locked dependencies. Opening the workspace performs no installation or
execution.

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
| Create/check isolated Python venv | Explicit installed absolute bootstrap interpreter; local venv and bundled pip |
| Verify Route Lab package / test its checks | Node; included original package |
| Reimport Route Lab in Blender | Blender; package source and export beside the verifier |
| Verify authored map routes | Verified venv Python; four Ember Rite JSON plans and current `measurements.md` |
| Verify/test authored map balance | Verified venv Python; atlas source plus `games/yuga-rust/src/ritual.rs` and `assets/vanara-sena.json` |
| Test Ember Rite solo movement and audio | Node; existing listener and solo-simulation tests, separate from a live room |
| Test Rust authority | Cargo; full `games/yuga-rust` source and lockfile |
| Build Rust browser package | Existing `build_web.py` through venv Python, installed locked dependencies and the documented Rust/WASM toolchain |
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
adds six focused specialists, and binds twelve role contracts and thirteen
development gates. The update preserves the prior ten roles, owner-edited
contracts and completed gates; it appends two specialists, six gates and five
versioned current-source handoffs. A real setup receipt contains the actual
employee IDs; a kit file does not mean the owner's live workspace was changed.

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

The current authored-map next gates extend the documented isolated Mandala slice
into Monsoon: ordinary dry paths, selected solids, both legal interactions,
interruption/reset/side swap and authoritative event ordering, with folds closed
initially. Listener-scoped audio and accepted hero contact timing feed the
ten-seat/two-rendered-client gate. The optional Unreal experiment does not block
this production path.

## Validation record

[validation.json](validation.json) records commands actually run for this scoped
integration. The five package tests include negative cases for corruption,
external buffers, wrong scale, moved/missing spawns, stale evidence and path escape.
Their earlier acceptance remains historical. The Python helper tests challenge
invalid paths and site-package settings, create a real disposable venv and run
the current authored routes, balance audit and two balance tests inside it:

```sh
DAFTAR_TEST_PYTHON=/absolute/path/to/python3 node --test tools/daftar-development/python-workspace.test.mjs
```

The five tests include an executable Windows-layout regression which permits the
standard-library roots and rejects both base package directories. Without the
explicit test interpreter, the two Python execution tests are skipped; the three
rejection tests still run. The authored checks retain their
analytic scope. Full game execution,
engine collision/navigation, GPU profiling, Unreal import/render and live model
inference remain separate work.

### Native design-contract repair

The original design-only hero catalogue still binds the exact pre-preface
master bytes from `c6f3b49`, preserved in
`games/yuga-native/tests/fixtures/contracts/production-6v6-v1-design-master.md`.
The design master at `83a67acf` differed from that snapshot only by the dated
Ember Rite competitive-direction preface introduced by `59f9cea` and updated by
`d5dc24b`. The live design can continue evolving. The TypeScript roster and
simulation pins remain tied to their live sources. The catalogue bytes and
its downstream Arjuna authoring receipts are unchanged. The frozen
`production-6v6` contract verifies the same historical bytes without changing
its descriptor, revision or wire catalogue. Neither validates playable 5v5,
native collision, or Unreal integration.

The Route Lab interchange directory carries `.gdignore` so headless Godot
native-game imports do not depend on configuring Blender. Copy the GLB to a
separate lab scene if you want to exercise a manual engine import.
