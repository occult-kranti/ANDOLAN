# REA/native-provider restore receipt

Restored the existing pinned developer tools without changing repository files. This packet prepares a separately assigned native-component analysis; it is not a game reconstruction or graphics result.

- REA CLI: `/workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs` (`6.5.0`; version/help pass).
- Ghidra: `/workspace/tooling/yuga-native-analysis/ghidra_12.1.4_PUBLIC` (`12.1.4` in installed application metadata).
- Java: `/workspace/tooling/yuga-native-analysis/jdk-21.0.12.1+1` (`21.0.12.1+1-LTS`; executed version passes).
- Python providers: `/workspace/tooling/yuga-native-analysis/python/bin/python` (34 exact pinned distributions match; capstone, pyelftools, Unicorn and pwntools import; `pip check` passes).

`commands.json` preserves each executed install/readiness command, exit code, elapsed time and log digest. `source/` and before/after pins retain the unchanged repository setup inputs. `root-package-verification.json` records fresh root-tarball SHA-512 and both registry signatures; `installed-rea-source-integrity.json` compares all 1,650 regular REA files with that verified tarball. `native-tool-records/` retains license/version/installation records and `native-installed-file-pins.json` pins critical installed files. `python-install-report.json` retains pip archive hashes; those are observed artifact identities, not repository-provided expected wheel hashes.

Install commands ran with inherited HTTPS proxy and CA trust, verification enabled, on CPUs 0 and 1. Native archives were checked for exact size/SHA-256 before extraction and removed by the unchanged repository installer. No native analysis, old C fixture, render, import or export ran. No persistent MCP configuration or cloud draft was changed; existing documented restore instructions remain the reusable route.

For the next separately authorized analysis process, use these environment selectors without replacing inherited authentication or trust:

```sh
GHIDRA_INSTALL_DIR=/workspace/tooling/yuga-native-analysis/ghidra_12.1.4_PUBLIC
JAVA_HOME=/workspace/tooling/yuga-native-analysis/jdk-21.0.12.1+1
GHIDRA_HEADLESS_MAXMEM=768M
REA_PWNTOOLS_PYTHON=/workspace/tooling/yuga-native-analysis/python/bin/python
```

The next owner must use the assigned exact local component and a fresh output directory. Root owns the analysis wrapper and heavy CPU scheduling. Optional Frida/native-addon, browser, terminal and other REA providers were not qualified. Whole-dependency signatures were not freshly audited. The toolchain remains outside shipping runtime/assets.
