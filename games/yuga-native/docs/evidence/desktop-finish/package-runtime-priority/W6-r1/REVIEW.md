# Explicit pipeline-priority runtime variant

Source-only support is ready. `--linux-runtime-variant pipeline-low-priority` requires the paired runtime binary and provenance arguments. It admits only the reviewed e69 binary and exact one-patch proof, while the official f64 editor remains the exporter and font-proof engine. No gameplay, model, renderer quality setting, Windows payload behavior, existing archive, or runtime binary changed here.

The existing Python fixture passes **50/50** (the previous 30 checks remain); it uses tiny temporary binaries, mocked version calls, and real tiny ZIP assembly, with no engine or PCK export. A separate compatibility comparison passes **5/5**: unchanged dce provenance, default/dce/Windows README bytes, and complete dce notice payload bytes. [W3's independent review](../../package-native-review/W3-patched-runtime-r1/REVIEW.md) passes 23/23 and preserves its original wording-only fixture correction.

The patched manifest uses `patched-public-source-template-debug` and `pipeline-low-priority-v1`, with source patches=1. Eleven pinned source/build/license records include the pristine source archive, baseline and patched build histories, exact patch, and before/after headers. Patched-only `bundled_evidence` paths retain full relative paths so identically named historical receipts cannot overwrite one another. The complete mapped closure is rechecked after copying. START-HERE and Linux NOTICE explicitly describe the modified runtime, separate official exporter, and limits. Every package continues to record `not_executed_by_packager`.

Crossed dce/e69 proofs and variants, missing evidence, altered expected manifest/proof mappings, and corruption of an earlier copied proof are rejected. Existing default and dce paths remain unchanged. This fixture is already registered in native CI and setup; no new workflow entry is needed.

The two independently fresh e69 diagnostic cold routes are evidence for the runtime decision, not execution of a future e69 ZIP. The former dce package and failed cold run remain unchanged. A new exact source checkpoint, fresh export/package, and actual extracted-package qualification are still required. The f8 release transport remains held and must be regenerated for successor assets and source.

## Validation commands actually run

```sh
python -m py_compile tools/package-native.py
python tests/package_linux_runtime_cases.py --report docs/evidence/desktop-finish/package-runtime-priority/W6-r1/focused-r1.json
python tools/package-native.py --help
python docs/evidence/desktop-finish/package-runtime-priority/W6-r1/compatibility_audit.py
```

The focused fixture completed with exit 0 in 0.080 seconds. The compatibility script, help, compile, and scoped diff checks also completed with exit 0. No extra engine, build, download, full suite, export, or publication was run.

## Later package invocation — not executed

After the lead verifies the successor source and restores the existing owned checkout, run from its `games/yuga-native` directory using the existing package workflow:

```sh
python tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --linux-runtime /workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority \
  --linux-runtime-variant pipeline-low-priority \
  --linux-runtime-provenance docs/evidence/desktop-finish/G0/template-priority-build-r1/finished-build-verification.json \
  --build-dir /workspace/scratch/yuga-desktop-integrated-package-r4/build
```

This command is a prepared recipe only. The lead still owns the exact source commit, storage release, execution grant, and fresh artifact qualification.
