# Overwatch: native-analysis intake and actual blockers

Audit: 16 October 2026, America/New_York. This is a tool/input readiness audit for the user's request to study the complete game before building a native YUGA. It does **not** mark Overwatch as reverse engineered. [Machine-readable evidence](OVERWATCH_NATIVE_INTAKE_EVIDENCE.json) records exact pins, file hashes, read scopes and executed checks.

**Finding:** the selected open-source tools can inspect game data or compile custom Workshop rules. They do not supply Overwatch's complete commercial client, authoritative server, renderer or production services. No Overwatch game installation, executable, server artifact or recorded reference match has been selected or supplied to this analysis. The available source studies therefore cannot establish full reconstruction or current-game behavior.

## What is present and what it can do

| Tool / exact source revision | Verified capability and entry point | Required inputs / current gap |
| --- | --- | --- |
| [OWLib](https://github.com/overtools/OWLib/tree/546efa19516d7df7ba138802d221c73ad886df28), `546efa19516d7df7ba138802d221c73ad886df28` | `DataTool/Program.cs` dispatches list/extract tools and opens an Overwatch installation through `TACTLib.ClientHandler`. `TankLib` contains selected resource/animation readers reviewed earlier. README entry: `DataTool.exe <overwatch_directory> <mode> [mode args]`. | A compatible, complete installed game directory and required local text/speech content. The source detects product/build, and explicitly reports that tool updates may lag a new game build. No installation was opened here. |
| [OverPy](https://github.com/Zezombye/overpy/tree/5a7d0e294b8cad73b9701987bb584d0551d7fa4d), `5a7d0e294b8cad73b9701987bb584d0551d7fa4d` | Version 9.7.17; `src/cli.ts` converts `.opy` text to Workshop text and Workshop text back to `.opy`. Built CLI: `node out/overpy_cli.js`; generated standalone compiler module is also required. | An OverPy/Workshop script and dependencies to build the compiler. Generated rules still execute inside the actual game's Workshop. Its “decompile” command does not decompile the Overwatch executable. |
| [Deltin / OSTW](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/tree/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd), `41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd` | `Deltinteger/Deltinteger/Deltinteger.csproj` builds the independent scripting compiler/tool. README describes conversion to Overwatch Workshop. Earlier selected tests cover rule/event semantics. | Compiler source and dependencies, then script text; the game remains the execution environment. No standalone Overwatch match simulation is established by these files. |
| [REA source documentation](https://github.com/morluto/rea/tree/d52a488476e7c41f573f23a1965d3f32d4e6a7f2), `d52a488476e7c41f573f23a1965d3f32d4e6a7f2`; installed package `rea-agents` 6.5.0 | Native overview, functions, assembly, references and pseudocode through a separately installed provider. Node entry: `/workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs`. | An explicit local binary and a configured compatible provider. Neither a game target nor a native provider was ready in this check. Installed package reports no build commit; the documentation pin is not asserted to be its runtime build hash. |

The three Overwatch reference repositories are no-checkout Git caches under `/workspace/tooling/overwatch-research/`; each working directory contains only `.git`. Earlier and new selected text files live in separate evidence folders. Having these repositories cached does not mean their tools are installed or executable.

## Exact build prerequisites from inspected manifests

**OWLib:** `global.json` requests .NET SDK `10.0.100`, `rollForward: latestMajor`, no prereleases. DataTool targets `net10.0` and references TankLib plus two submodules: TACTLib `129f977b604b2576bfd048e0f2be8b44ee983f39` and revorbstd `c5f05f3756a2cd589ea0d0acd88046c59ee67b7b`. The workflow publishes Windows x64, Linux x64 and macOS arm64 outputs from a Windows runner; this is a declared build recipe, not a verified Linux runtime result. Package restore and platform-dependent conversion components still need an actual build/run check. `dotnet` is absent from PATH here. No submodule checkout, package restore, build or DataTool invocation was performed.

**OverPy:** `package.json` requests pnpm >=10.0.0. `esbuild.js` separately builds the `standalone` and `cli` targets; the CLI loads `./overpy_standalone` or `./overpy` before printing help. The build also copies a QuickJS WASM dependency. Node 24.19.0 and a pnpm launcher are present, but the reference cache has no source checkout, `node_modules` or built output. The compiler was not run. Building this tool could test our own scripts, but would not recover native game logic.

**Deltin:** its compiler project targets `net8.0` with `win-x64;win-x86;linux-x64` runtime identifiers. It has NuGet dependencies and content files for language definitions, modules, maps/elements and lobby settings. A full checkout, suitable SDK/restore and tests are needed before claiming a working compiler. No `dotnet` runtime/SDK or built compiler was found in this intake.

The OWLib README's Blender importer is a separate project and requires Blender >=3.5. Local Blender reports 4.3.2. The importer was not installed or audited here. Blender's presence alone establishes neither a successful import nor ready-to-use original YUGA characters.

## REA readiness actually executed

Both commands completed with exit code 0:

```sh
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs --help
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs providers --json
```

The second command reports:

- **Ghidra unavailable / not configured:** expects `GHIDRA_INSTALL_DIR` pointing to an extracted Ghidra 12.1.x release. No headless launcher or matching native decompiler was found. The Java check reports Java 21.0.12.1, “runtime only,” and does not establish a suitable full JDK.
- **Hopper unavailable:** launcher `/opt/hopper/bin/Hopper` missing or not executable.
- **IDA unavailable / not configured:** no upstream MCP registration configured; no live connection probed.
- **No binary open; every native provider's target support unknown.** Static managed-metadata capabilities are separately available; they do not establish that the native Overwatch client is a .NET assembly or that it was inspected.

These are readiness observations, not successful binary analyses. No `inspect`, `decompile`, game launch, target attachment or game-data extraction was run. No provider setup or configuration was changed. This audit adds zero commercial-game REA analyses.

## Input contract for the next substantive analysis

1. **Identity first:** select an actual local game installation or selected binary, state the exact game build, platform and provenance, and record SHA-256 and size. Keep it outside the distributable YUGA tree. A GitHub tool checkout is not this input. The checked research/cache folders contained none of the installation/executable/capture filename patterns listed in the evidence record; this is not an exhaustive search of the filesystem or the user's devices.
2. **Separate targets:** use a client executable for static instruction/function questions; use a compatible game-data directory for resource-format inventory; use exported Workshop text for custom-rule compilation. Do not substitute results from one for the others. Server-only code/services require separate evidence: a client artifact cannot itself establish the implementation of unavailable authoritative services.
3. **Prove a provider on an explicit benign fixture first:** install/configure a compatible native provider and full JDK where needed, re-run readiness, and retain a fixture analysis with input hash and coverage. The source-documented first game-target command would be `rea inspect /absolute/path/to/selected-binary --provider ghidra --json`; it has **not** been executed here. Verify target-format support rather than infer it from `.exe` or `.dll`.
4. **Choose a finite question and preserve unknowns:** for example, inventory resource references or identify the input-to-animation boundary in one exact build. Record selected functions, unresolved indirect calls, incomplete decoding and missing server paths. Full pseudocode output is not source recovery, behavioral equivalence or proof of playable reconstruction.
5. **Match observed behavior separately:** use a declared reference build and reproducible recorded scenario to measure movement, shot timing, ability transitions and presentation. No such recording was supplied or viewed in this pass. Original YUGA acceptance should use its own deterministic inputs and rendered motion, not silently transplant unverified constants.

OWLib needs an additional execution check before any future data inventory: `ToolFlags.Online` defaults **true**, and `Program.InitStorage` passes it into the client loader. The loader configuration also names a remote keyring; saved arguments and an environment-based installation override can affect the selected target. This audit did not fetch that resource, inspect key material or exercise protection recovery. An offline read-only inventory must first verify the loader's complete network and target-selection behavior with the selected version. Merely omitting an extraction mode is not evidence of offline operation. No game-data download, account sign-in, packet interception or protection bypass was attempted.

## Relation to native YUGA graphics

Native PC delivery removes a browser constraint; it does not turn resource readers or decompilers into a finished renderer and art team. The concrete original-asset track remains: detailed meshes and topology, PBR textures, stable rigs, authored/blended motion, readable ability effects, lighting, sound and measured rendering budgets. “4D” is treated here as animated 3D over time, not a distinct demonstrated graphics technology. No commercial model, animation, texture, map or sound was extracted or added to YUGA by this audit.

OWLib's inspected tool license is MIT; OverPy is GPL v3. Deltin's previously inspected MIT notice is in the extension subtree and does not by itself resolve every sibling compiler file's reuse scope. Tool licenses are separate from the rights to game data those tools can read. The prior [Overwatch engineering study](OVERWATCH_ENGINEERING.md) records the selected animation/Workshop source findings; this intake does not expand them into whole-engine claims.

**Practical next step:** complete native-provider readiness while the original YUGA scene/art work proceeds independently. Begin commercial-target analysis only when a concrete local artifact and its build identity are available; the first deliverable is a hashed offline inventory and one verified subsystem question. Full-engine reconstruction remains unestablished and cannot be honestly marked complete from the available inputs.
