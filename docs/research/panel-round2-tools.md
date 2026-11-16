# Panel round 2 — source preparation and REA qualification

Date: 15 November 2026. Product: YUGA native desktop. Source baseline: `7162b5d0` on `work/yuga-studio`. Owner: tools/platform researcher. Exclusive versioned changes: `tools/research/prepare-open-source.py` and this report. Read the local YUGA models/build and evidence-review skills, native handoff, build handbook and build-farm guidance.

## Panel decision

Round 1 established that renderer substitution is a separate integration project. Round 2 adopted four source-only references around the existing Godot product: GDQuest controller/UI code, REA static analysis, Rapier physics reference, and HyperFrames capture implementation. No reference code or assets were imported into the product. Source preparation does not count as completed art, matches, hardware performance or a released game.

The other researcher owns [the 15-entry catalog](../../tools/research/opensource-catalog.json). Only `gdquest-tps`, `rea`, `rapier` and `hyperframes` are enabled there. Prometheus remains deferred: no proprietary client, injector runtime or game data was acquired. GDQuest root license grants MIT for code and CC-BY-NC-SA-4.0 for art; the nine-file sparse intake excludes its art and scenes.

## Implemented helper

[prepare-open-source.py](../../tools/research/prepare-open-source.py) uses Python standard library and Git. It supports `--list`, explicit `--fetch ID ...`, and `--catalog PATH`. All selected entries are checked before a fetch starts: exact HTTPS GitHub URL, full 40-hex commit, explicit source-only approval, no proprietary-asset requirement or product import, literal sparse paths, license paths and a maximum budget no greater than 256 MiB.

Git runs with lifecycle hooks, system/global config, system attributes, executable symlinks and recursive submodules disabled; no upstream installer, build script, LFS filter or catalog-supplied command is run. Fetch is filtered (`blob:none`), depth one and exact-commit, followed by sparse detached checkout. Git commands have a 120-second timeout and per-file size cap; the total checkout budget is checked after phases. This is a preparation guard, not an OS sandbox or a strict total-download limit during each Git operation.

New sources stage in a fresh local directory. Successful receipts retain canonical URL, commit, catalog hash, sparse paths, actual license SHA-256, file/byte inventory and timestamp. Existing sources are never reset or replaced: receipt, origin, HEAD, license hashes and clean status must match. Symlinks, dirty directories and unreceipted directories are refused and preserved. Failed staging remains for inspection. All source/license hashes matched the reviewed catalog.

Run from the repository root:

```sh
python3 tools/research/prepare-open-source.py --list
python3 tools/research/prepare-open-source.py --fetch gdquest-tps rea rapier hyperframes
```

## Actual source preparation

Fresh preparation and an immediate existing-source verification both exited 0. Results live in ignored `.local-tools/research/`; they are local reproducible tooling, not shipped game files.

| ID | Exact revision | Sparse files | Source bytes | Total bytes including Git |
| --- | --- | ---: | ---: | ---: |
| gdquest-tps | `b3bd6e81084f568be8aa44a69a0c2b1e52e806b3` | 9 | 45,290 | 132,115 |
| rea | `807dd1742f731ad4a0dba34176527eb248b848a2` | 5,331 | 46,925,184 | 61,327,728 |
| rapier | `475caa3ff4646fd9a796b67d14116256f4962bc7` | 243 | 3,242,491 | 4,409,779 |
| hyperframes | `e2430edecf5492a02a363eaa5c30ad2708af5aee` | 1,287 | 10,949,481 | 16,107,318 |

Total: **6,870 source files, 61,162,446 source bytes, 81,976,940 bytes including Git**. Each source remains below its 150 MiB catalog budget.

| ID | Actual license SHA-256 |
| --- | --- |
| gdquest-tps / LICENSE | `c298531e638430618d5f68ca9e1be23d3e6510173aa764068c3f7e3fcf25d140` |
| rea / LICENSE | `798f9e4d18e49b30bf2f12696c8ced73dc4e1413da375a333d01281543a1ea8b` |
| rapier / LICENSE | `ceacfa4d7fa67df64ab09a56fe248c50a3bfc9bc00374d69bd74ad763b14b89c` |
| hyperframes / LICENSE | `4259155fb06f127687ee7b0a8a3682d45132db0f2da26cbc0b7a2d1e796436b8` |

Per-source receipts: `.local-tools/research/receipts/{gdquest-tps,rea,rapier,hyperframes}.json`. Catalog SHA-256 at preparation: `fc72d484d7f94285ab29cd79ba729bceedfd57570c8698fe4a45482b1858405d`.

## Exercised counterexamples

The retained `.local-tools/research/qa/receipt.json` records **7/7** cases with actual command output:

1. Unknown source ID is rejected before fetching.
2. Deferred Prometheus ID is rejected.
3. A `file://` repository URL is rejected.
4. A symbolic revision (`main`) is rejected.
5. A preexisting directory without a receipt is refused; its marker hash remains unchanged.
6. A source with new untracked work is refused; its marker survives unchanged. Only that test-created marker was then removed.
7. All four clean prepared sources verify again with exit 0 and no reset.

`python3 -m py_compile tools/research/prepare-open-source.py` and `--help` also passed. The preservation fixture remains local for review. No persistent test fixture was added to the game suite.

## REA: actual isolated execution

The build owner installed **rea-agents 6.5.0** at `/workspaces/tooling/rea` using the existing `docs/research/rea-tool-package{,-lock}.json`, `npm ci --ignore-scripts` and no persistent MCP registration. The saved lock SHA-256 is `73fa03d670870e8234e7823bca98e8cd846773fb661819ffe48a5bbb6728c7dd`; package tarball integrity remains the recorded SHA-512 from the earlier REA runbook. The root package and game dependency manifests were not changed for REA.

This researcher inspected the installed package metadata and dispatcher before executing `--version`, `analyze-javascript-application --help` and one bounded analysis; all exited 0. The analyzer statically parsed the owned `games/yuga/client/practice-goals.ts`, using 512 MiB analyzer heap and a 30-second analysis timeout. It processed one selected file / 7,364 text bytes / 1,243 AST nodes, reported zero parse failures and zero integrity contradictions. All three exported function names (`startPracticeGoal`, `updatePracticeGoal`, `practiceGoalProgress`) appear in its retained semantic graph; their names were independently read from the source as a narrow oracle. 183 inventoried files remained outside semantic analysis. No target application code was executed.

```sh
node /workspaces/tooling/rea/node_modules/rea-agents/scripts/rea.mjs --version
node /workspaces/tooling/rea/node_modules/rea-agents/scripts/rea.mjs analyze-javascript-application games/yuga --source-path client/practice-goals.ts --max-heap-mb 512 --analysis-timeout-ms 30000 --format json
```

Analysis took 3.385 seconds on this CPU host; this is tool execution timing, not game performance. Receipt/output live in `.local-tools/research/rea-qualification/`. The output SHA-256 is `9fe40913edd252b3a0d8b4cbd5f8523abfcc9cb4cf1e68daed9d3da25ac5b90a`; analyzed file SHA-256 is `6dc8311d128d84d8333414e627a734f0fc69c67482cd9eebfab9ae9862ae7dd4`. A reporting helper initially treated `unselected_files` as a list and raised TypeError; it was corrected to the returned integer without rerunning or altering REA output.

The install reported seven dependency advisories (five moderate, two high); no automatic dependency rewrite was applied. The optional native providers remain unqualified because lifecycle scripts were intentionally disabled. During parallel setup, this researcher also completed an identical isolated install at `.local-tools/rea-runtime` before receiving the build owner’s coordination message. It is an unused duplicate of the same lock; the qualified path is `/workspaces/tooling/rea`. Both remain outside Git; no independent capability is claimed for the duplicate.

## Readiness and next owner

- **Ready:** source browsing at exact pins, clean-source verification, license receipts, REA CLI and the specific static TypeScript analysis path above.
- **Not built or run:** GDQuest complete demo, Rapier native/Wasm physics, HyperFrames video renderer, Raea, ThreeRT and every other deferred catalog entry. Source availability is separate from execution.
- **Core build owner:** Godot/Blender/FFmpeg/Xvfb installation and runtime capture are separate receipts; this tooling work did no heavy renders.
- **Next game owner:** borrow ideas from source with project license notices and focused behavior tests when actual code is adopted. Keep native captures and input evidence as the acceptance gate.

Research count: round 1 used 35 Exa search result slots and 10 direct primary fetches; this tooling round added **zero search slots**. The catalog owner separately fetched three primary pages in round 2. Source fetch/execution counts are reported above and must not be relabeled as additional research sources or completed game screens.
