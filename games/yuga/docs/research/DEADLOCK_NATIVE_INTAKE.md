# Deadlock native analysis intake

16 October 2026 (America/New_York). This audit answers what we can actually run against Deadlock, which inputs are missing, and how the native workflow differs from the completed community-source studies. It does not describe the existing lane lab as a reconstructed Deadlock engine.

**REA supports native compiled binaries. The immediate gap is the absent game input and, at this audit's start, an unconfigured deep-analysis provider.** The old TypeScript studies used only one part of REA. We executed native header, symbol and assembly inspection on an existing MIT-licensed tool fixture in this pass. No Deadlock client, replay or commercial resource was analyzed. Exact commands, return codes, source hashes, output hashes and retained paths are in [DEADLOCK_NATIVE_INTAKE_EVIDENCE.json](DEADLOCK_NATIVE_INTAKE_EVIDENCE.json).

## Input inventory

A filename census checked 6,847 files across `/workspace/ANDOLAN`, `/workspace/research` and `/workspace/tooling`, excluding generated dependencies, build/test output, Git metadata and attachments. It found no `.dem`, `.vpk`, compiled Source 2 model/map/material/animation suffixes, `citadel.exe`, `client.dll`, `server.dll` or `appmanifest_1422450.acf`. This is a scoped filename result, not a byte-signature scan or a claim about every file on the host. Credentials and attachments were not inspected.

| Input | Observed state | What it would establish |
| --- | --- | --- |
| Exact Deadlock installed-client build and selected executable/library | Not supplied or located in the audited trees | Local compiled instructions, imported/exported names, references and recoverable pseudocode. Build identity is needed before comparing versions. |
| Compatible recorded `.dem` match | Not supplied or located | Recorded tick/entity/event observations, with parser/build compatibility limits. |
| Timestamped reference video of the same controlled scenario | No local reference match identified; none watched in this audit | Visible motion, anticipation, release/recovery, camera and effect timing for comparison with recorded events. |
| Compiled resource packages/models/materials | Not supplied or located | Decoded resource data where a format tool supports the exact version. Successful conversion alone does not recover the original scene/material/animation authoring pipeline. |
| Commercial server/backend source | Not present | Cannot be inferred in full from a client or replay. |
| Community sources | Present as selected files | Boon, Haste, Deadlock API and other previous source studies. These are tools/prototypes, not the shipped engine. The Boon/Haste directories lack their build manifests and are not runnable complete checkouts. |

## Actual REA capability checks

The executed package is **`rea-agents` 6.5.0**, MIT, at `/workspace/tooling/rea-runtime/node_modules/rea-agents/`. The separate REA source checkout is commit `d52a488476e7c41f573f23a1965d3f32d4e6a7f2`; its documentation is corroborating evidence, not a substitute for installed-runtime identity.

We ran `--help`, `providers --json`, `capabilities --json`, `doctor --json`, and help for `analyze`, `decompile`, `inspect-artifact` and `inspect-binary-layout`.

- `analyze PATH --provider ghidra` and `decompile PATH PROCEDURE --provider ghidra` are real native routes. Ghidra exposes inventory, assembly, pseudocode, call/reference and bounded value-flow observations. Recovered pseudocode is not original source.
- `inspect-artifact` inventories supported packages. It is not a Source 2 VPK/model/animation renderer. Source 2 format decoding is a separate tool stage.
- `inspect-binary-layout` accepts ELF input through the pwntools adapter. Its installed profile requires an explicit Python with **pwntools 4.15.0, pyelftools 0.33 and Unicorn 2.1.2**, and bounds input to **32 MiB**. That bound is not a Ghidra limit and can matter for a large game module.
- `inspect-with-objdump PATH OPERATION` already works with the installed GNU objdump. It records native command output and before/after target identity; it does not recover a complete application graph or source project.

The initial broad doctor exited 1. Ghidra was unconfigured, Hopper absent, IDA unregistered; Node 24.19.0 was healthy. Java 21.0.12.1 was a runtime-only installation with no `javac`. Missing optional integrations in that broad result do not invalidate the objdump path that was actually exercised.

### Native fixture proof performed here

We compiled the existing REA MIT fixture `scripts/fixtures/binary-layout.c` with:

```sh
cc -g -O0 -fno-inline \
  /workspace/tooling/rea/scripts/fixtures/binary-layout.c \
  -o /tmp/yuga-deadlock-native-fixture
```

Compile exited 0 and produced a 17,920-byte artifact, SHA-256 `17fcf295403b79c9d97e4af4694fded29692ce6a5ea17e1c12cea0c61c6f1e21`. The fixture was **not executed**.

`inspect-binary-layout` initially exited 1 with an explicit missing-pwntools-profile error. That failed probe remains recorded. We then executed these three supported inspections:

```sh
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  inspect-with-objdump /tmp/yuga-deadlock-native-fixture file_headers --json
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  inspect-with-objdump /tmp/yuga-deadlock-native-fixture symbols --json
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  inspect-with-objdump /tmp/yuga-deadlock-native-fixture disassemble --json
```

All three exited 0, reported no output truncation, and preserved the artifact hash. Observed header: ELF64 x86-64, entry `0x1050`; symbol/assembly outputs include `read_values`. Evidence IDs end in `5890ae23`, `88aeafd` and `9bbdbb8`, respectively; the JSON retains their full values. This proves an executable native inspection path on that small known fixture. It says nothing about Deadlock completeness or rendering quality.

### Deep-provider prerequisites and footprint

REA accepts Ghidra **12.1.x**, with its bridge verified upstream against **12.1.4**. It needs the full 64-bit JDK declared by that release's `application.java.min`/`max`, a matching host-native decompiler, `support/analyzeHeadless` and a procps-compatible `ps`. On this Linux x64 host the decompiler belongs under `Ghidra/Features/Decompiler/os/linux_x86_64/`. Configure `GHIDRA_INSTALL_DIR` explicitly and select the full JDK without replacing unrelated system configuration.

`GHIDRA_HEADLESS_MAXMEM` controls the Java heap; default is 2G. Upstream documents 512M for small fixtures. That does not cap total process-family RSS. The CLI exposes startup timeout configuration; a large commercial module may require materially more time/memory than the fixture. No full-game sizing or performance was measured here. Ghidra uses ephemeral analysis databases and does not rewrite the selected executable.

A parallel toolchain task is provisioning Ghidra/JDK and the exact ELF dependencies and testing an original combat fixture. **The initial availability findings above are a timestamped pre-provision observation.** Its separate installer, fixture and `native-analysis-toolchain.json` own subsequent results; this document does not predeclare success.

## Concrete Deadlock entry points once inputs exist

1. **Bind an input to a build.** Record the supplied installation/build manifest, selected files, SHA-256, size and acquisition/source context. Keep an untouched copy outside the shipping game. Choose a concrete question such as “what local input reaches this projectile release?” rather than labeling the entire install analyzed.
2. **Inventory and inspect one module.** Execute `inspect-with-objdump INPUT file_headers --json` first when GNU objdump accepts the format. After provider readiness, execute `analyze INPUT --provider ghidra --json`; select an observed procedure/symbol/address, then `decompile INPUT PROCEDURE --provider ghidra --json`. Keep function coverage, indirect-call unknowns and missing symbols. A PE client is not an input to the ELF-only layout command.
3. **Measure one recorded scenario.** The pinned Boon README at `0c7663f17aa24a65374925b022fd4d98aaa47477` documents `boon info match.dem`, `boon show match.dem kills --limit 20`, and Python `Demo(path, preload=False)` followed by selected dataset loading. These are documented entry points, **not commands executed here**; Boon is not installed in this audit snapshot. First verify replay compatibility and metadata, then request player state, damage, abilities and objectives; opt into large trooper datasets only for a bounded lane question. Retain pause/tick/game-time distinctions and missing fields. No chat dataset is needed.
4. **Cross-check where valuable.** Haste's pinned README at `7ce32e67ba107f256777a10fe0cb19b7812dd187` documents `cargo run --example deadlock-position -- match.dem` and the `deadlock-gametime` example. Its existing directory is only selected source and `cargo` is absent in the initial snapshot, so this route needs an inspected complete pinned checkout/toolchain before execution. It is a potential independent check, not a second result already obtained.
5. **Study visual formats separately.** The previous [format-tool study](../../art/DEADLOCK_VIDEO_AND_TOOLING.md) identifies ValveResourceFormat/Source 2 Viewer and documented animation/material limitations. No viewer executable or resource payload was present here; no new viewer command has been validated. Recovered compiled meshes/animation curves would inform analysis of an exact input, not automatically grant complete shaders, cloth, collision, authored source or redistribution rights. YUGA's shipped assets require their own creation/reuse provenance.

## What a complete claim would require

A native client can expose local behavior, but server-only arbitration, matchmaking, anti-cheat, accounts and backend state remain unavailable unless separately supplied and examined. A replay is an observation of a match, not the complete algorithm generating every possible match. A decoded animation/model is a compiled representation, not the original motion-capture, rig-control, shader-authoring or lighting pipeline. Compiler optimization, missing symbols and indirect dispatch leave unresolved behavior even after a decompiler finishes.

The useful acceptance path is therefore a versioned coverage matrix: client systems, observed gameplay rules, assets/formats and network/backend boundaries, each with an input, a reproducible question, output evidence and explicit unknowns. “All files passed through a tool” does not establish complete reconstruction. Moving YUGA to a native renderer may improve rendering budgets; REA itself does not generate production models or automatically produce Deadlock-quality art. Time-based 3D animation, VFX, lighting and camera work need separately measured original production work.

**Next actual Deadlock step:** receive a build-identified legitimate installed-client module or compatible `.dem` replay, then run the matching workflow above and compare a narrowly defined movement/shot/economy event with a timestamped controlled recording. The native toolkit and original game build can advance while that commercial input is absent. No client download, credential access, process attachment or network/protection bypass was performed by this audit.
