# Native REA toolchain acceptance

This folder verifies actual binary inspection and Ghidra decompilation using an
original, small C fixture. It is **not a reconstruction of Deadlock or Overwatch**.
The source has debug symbols, uses `-O0`, and contains a deliberately simple damage
rule. This proves the local providers work; it does not measure coverage of an
optimized or stripped commercial game.

The recorded run passed compilation, five executable fixture cases, REA ELF
layout inspection, Ghidra decompilation, and a selected-function dossier query.
Ten assertions check the returned evidence and binary identity. The dossier
recovers the direct calls `main → combat_damage → clamp_armour`, six basic blocks,
and 36 assembly lines. Its reported complete relationship coverage applies only
to the selected 97-byte `combat_damage` function. Targetless indirect calls and
runtime behavior remain outside that coverage.

The compact proof is
[native-analysis-toolchain.json](../../docs/evidence/native-analysis-toolchain.json).
Full raw outputs from the recorded run remain at the `raw_evidence_directory`
listed there. Pseudocode is reconstructed output, not original source.

## Reproduce

Use Linux x86-64 with Python 3.12, a C compiler, Node compatible with REA 6.5.0,
and approximately 2 GB free disk. The tools are installed outside the repository.
The installation uses normal HTTPS through the inherited network configuration;
no credentials, system package changes, or client MCP registration are required.

```sh
python games/yuga-native/tools/native-analysis/install-toolchain.py \
  --root /workspace/tooling/yuga-native-analysis

python -m venv /workspace/tooling/yuga-native-analysis/python
/workspace/tooling/yuga-native-analysis/python/bin/python -m pip install \
  -r games/yuga-native/tools/native-analysis/python-requirements.txt

python games/yuga-native/tools/native-analysis/verify-toolchain.py \
  --tool-root /workspace/tooling/yuga-native-analysis \
  --rea /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  --output /workspace/tooling/yuga-native-analysis/evidence/new-attempt
```

`--rea` must point to an existing REA 6.5.0 CLI. A new output directory is required
to preserve prior evidence. The verifier saves every command, exit code, duration,
stdout/stderr digest, raw provider output, and acceptance result. It caps each
command at 180 seconds and the Ghidra heap at 768 MB. Only the authored fixture is
executed; REA does not launch it.

The installer pins official Ghidra 12.1.4 and Eclipse Temurin JDK 21.0.12.1+1
release assets by exact byte count and SHA-256 from their GitHub release metadata.
It verifies archives before extraction and removes the archives afterward.
Matching receipts allow an existing installation to be reused; those receipts
are not a fresh integrity scan of every installed file. The separate Python
provider requirements pin the versions used for this run, including REA's exact
pwntools 4.15.0, pyelftools 0.33, and Unicorn 2.1.2 requirements.

No commercial game inputs were supplied. Analysis of those games still requires
exact local game artifacts and version identity; this fixture cannot substitute
for those inputs or recover server implementations absent from a client package.
