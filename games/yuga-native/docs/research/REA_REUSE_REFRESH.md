# REA reuse refresh for YUGA

17 October 2026. This pass reuses the existing REA development-tool lane and
checks current forks against exact commits. The useful path is **REA evidence →
one bounded implementation question → independent source/behavior comparison**.
The ten inspected forks provide no demonstrated implementation advantage over
the inspected upstream. The [source and claim ledger](rea-reuse-refresh.json)
records exact reads, licenses, compare responses and execution boundaries.

## Three bounded checkpoints

| Checkpoint | Result |
| --- | --- |
| 1. Inspect retained setup and current cloud state | Existing runbooks and historical C-fixture evidence were retained, but the external REA/native-tool installations were absent. Current ordinary authenticated `gh api` requests worked. No old fixture was repeated. |
| 2. Pin upstream, licenses and fork differences | Upstream `300905c11be1c25b98fda9e2b71dfa899fc2831c`; complete 4,656-entry tree; selected ranges of ten source/doc files; ten fork comparisons. Eleven inspected license files are byte-identical MIT. |
| 3. Restore and exercise a real authoring component | Pinned REA 6.5.0, Ghidra 12.1.4, JDK 21.0.12.1+1 and 34 exact Python dependency versions restored. Fresh actual-component static checks pass: bridge9/9 and callback8/8. A separate five-call finite-guard oracle plus predicate/input checks passes7/7. These establish the bounded findings below. |

The current GitHub source checkpoint and installed npm package are separate
identities. Both declare version 6.5.0, but that label does not make their bytes
identical. The historical GitHub checkpoint is 142 ancestry commits behind the
current inspected head; that count is not a full implementation audit or a
reason to silently upgrade the verified npm package.

## What REA contributes

The selected README/native/Ghidra contracts describe local function discovery,
pseudocode, instructions, CFGs, symbols and references. Targetless indirect calls,
aliasing, runtime reachability and omitted value-flow data can remain unknown.
Ghidra's pseudocode represents its analysis of a selected body. REA supplies
those observations to an agent that writes and tests an implementation.

The JavaScript/ASAR lane parses selected local source as inert text and builds
static application graphs. Its inferred imports/calls do not establish runtime
execution. The nine-stage reconstruction-readiness report is an internal
repository conformance verifier, rather than a public whole-game reconstruction
command. The source-read boundaries are pinned in the ledger.

REA's README links DX-Ball sound-pan and TH04 bullet-ring reconstructions. Its
Touhou evidence notes describe oracle-driven function work and separately dated
playability/runtime milestones. Those are **upstream-reported examples**, not
games or historical compilers executed in this pass. The useful transferable
method is to preserve a failing comparison and verify literal data as well as
instruction relationships. The notes themselves describe how an unchecked
floating literal once let a wrong threshold appear exact.

## Fork comparison

The first eight entries of GitHub's newest-forks response were selected before
reading differences. All eight resolved to the same upstream commit. Two named
forks from the earlier retained study were then added as historical comparators,
keeping this pass at ten. This sample is finite and uses commits/diffs, not stars.

| Fork | Pinned head | Ahead / behind upstream | Actual difference / decision |
| --- | --- | --- | --- |
| `niksp220598/rea` | `300905c1…` | 0 / 0 | Identical commit; no implementation change. |
| `AbhikDe/rea` | `300905c1…` | 0 / 0 | Identical commit; no implementation change. |
| `jgt87/rea` | `300905c1…` | 0 / 0 | Identical commit despite a different push timestamp. |
| `abhi-techsavvy/Reverse-Engineer` | `300905c1…` | 0 / 0 | Renamed fork, identical commit. |
| `DivyanshVish/rea` | `300905c1…` | 0 / 0 | Identical commit; no implementation change. |
| `Giannicarducci/rea` | `300905c1…` | 0 / 0 | Identical commit; no implementation change. |
| `david1dinan/rea` | `300905c1…` | 0 / 0 | Identical commit; no implementation change. |
| `jin66god/rea` | `300905c1…` | 0 / 0 | Identical commit; no implementation change. |
| `MENAMarketer/rea` | `fc5c5fc4…` | 1 / 637 | One added 41-line `CLAUDE.md` for a marketing workspace; no native-analysis implementation addition. Its instructions remain source material. |
| `Doriandarko/rea` | `12ee785e…` | 0 / 1,259 | No fork-side new commits or changed files in the comparison. |

All ten pinned fork LICENSE files match upstream's 1,064-byte MIT text
(`798f9e4d…`). REA-authored code's MIT terms and third-party material/tool terms
remain distinct. No inspected fork was cloned, installed, executed or selected
as a new game foundation.

## Exact reuse and experiment

**Tool reuse:** the restored
`/workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs` supplies
CLI evidence through the existing pinned Ghidra/native-provider lane. Root's
`tools/native-analysis/inspect-component.py` is the small YUGA-facing adapter.
This is an offline authoring/investigation tool, with no new game runtime or
persistent MCP registration.

**Actual code/build input:** role 11 built the original thin YUGA bridge against
unmodified MikkTSpace C/header at
`3e895b49d05ea07e4c2133156cfa94369e19e409`. Its real shared library exports
`yuga_mikk_generate`, compiled with GCC 14.2, `-O2 -g -fPIC -shared`. The fresh
REA analysis uses this library, not the old deliberately simple C fixture.
The selected bridge dossier returns **46 basic blocks and 1,213 body bytes**,
with resolved `sqrt` and `genTangSpaceDefault` thunks. A supplemental `tangent`
callback dossier contains one block/43 bytes. Its source, assembly and pseudocode
agree on **`(face*3+corner)*16` bytes with sign at offset12**. Caller buffer lengths
remain a Python-wrapper contract; decompilation cannot prove the allocations
behind the C pointer arguments.

[Exact native evidence](../evidence/reuse-study/rea/native-component/summary.json)
retains every command/stdout/stderr and the unchanged 148,904-byte input SHA
`0f038e6f83f5fce5e10d0b8c14028f96ed7368229c59bded44a2512dda91bb4a`.
The nine main and eight callback checks verify identity/tool output; they are
separate from the [five native behavior calls and two predicate/integrity checks](../evidence/reuse-study/rea/native-component/finite-guard-oracle-repro.json).
That probe accepts a valid triangle (return0) and rejects NaN position/normal/UV
and infinite position (each return2).

A useful limitation surfaced: the optimized bridge's pseudocode has misleading
pointer casts from reused stack storage, and its finite guards appear as
max-float comparisons without an explicit unordered/NaN clause. The retained
assembly contains `UCOMISS`/`JC`; the actual native calls observe rejection. A
rendered IEEE comparison alone would return false for NaN. **No whole-function
source equivalence is claimed from this pseudocode.** Zero reported unresolved
calls applies only to the selected bodies, not the rest of Mikk or a game.

**Method inspiration:** exact input hashes, explicit unknowns, bounded function
questions, separately executed oracles and contradiction retention. No historical
commercial game code, model, texture, sound or map is imported by this pass.

The reproducible fresh-input command is:

```sh
taskset -c 2,3 python3 games/yuga-native/tools/native-analysis/inspect-component.py \
  --binary /workspace/tooling/mikktspace-yuga-r1/libyuga_mikktspace.so \
  --symbol yuga_mikk_generate \
  --tool-root /workspace/tooling/yuga-native-analysis \
  --rea /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  --output /workspace/scratch/rea-reuse-mikktspace-analysis-NEW \
  --timeout 180
```

Use a fresh output path and the current pinned input. The wrapper records ELF
layout, decompilation and a selected function dossier, checks input/provider
identity and retains raw stdout/stderr. It runs tools without executing the
input library. The separate finite-guard probe executes only the reviewed
component with known fully allocated buffers; role 11's broader numerical tests
remain distinct. Its reproducible helper is archived at
`docs/evidence/reuse-study/rea/native-component/finite_guard_oracle.py` and accepts
`--binary` and a fresh `--report` path. Its recorded repeat verifies that helper
and does not double the five-case coverage.

## Retained setup proof and next owner

[Restore receipts](../evidence/reuse-study/rea/restoration/summary.json) record
nine successful readiness/install commands, two verified root registry
signatures, all 1,650 installed REA package files matching the verified archive,
exact pinned Ghidra/JDK archive hashes, matching Python versions and dependency
checks. Small receipts/source/logs are retained; caches and the verified 5.6 MB
npm archive stay outside the repository. Root-package integrity is narrower than
all-dependency publisher provenance, and optional unexercised providers remain
unqualified.

Root owns integration. The selected-component checks are complete; the final
independent research audit is pending. Retain this developer-tool lane and role
11's actual Mikk reuse for the material-frame work, with its broader oracle and
actual output-art acceptance kept separate. The [open-game source audit](OPEN_GAME_CODE_REUSE.md)
provides the separate game-code/license comparison when available. Native
multiplayer/authority, final hero appearance and consumer-GPU performance keep
their existing acceptance gates. No supplied Deadlock, Overwatch or Dota 2
client was downloaded or recovered here.
