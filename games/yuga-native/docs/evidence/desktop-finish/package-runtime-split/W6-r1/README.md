# Explicit Linux exporter/runtime separation

The Linux runtime override is implemented and source-tested. No successor package has been exported or executed in this packet. The official-engine package and its blocked warm execution remain unchanged in [package-export-r2/W6](../../package-export-r2/W6/REVIEW.md) and [W1's actual execution receipt](../../package-native-review/W1-r1/receipt.json).

`--linux-engine` continues to perform PCK export and imported-font qualification. Without additional arguments it also remains the bundled Linux runtime, and both default Linux and Windows START-HERE bytes are identical to source `5542e61610d20e591effbed9dec15fd10398e31d`.

The paired `--linux-runtime` and `--linux-runtime-provenance` arguments admit only the reviewed unmodified public-source build:

| Role | Exact SHA-256 | Version |
| --- | --- | --- |
| Official exporter and font probe | `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3` | `4.6.3.stable.official.7d41c59c4` |
| Optional public-source Linux runtime | `dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f` | `4.6.3.stable.custom_build` |

The runtime is a community-built `template_debug` from public commit `35e80b3a8822a9df9be390814b62f44c0a9c69e8`. Fixed hashes bind its historical zero-patch build verification, build result, pristine source recovery, MIT license and third-party COPYRIGHT. The later diagnostic working source directory has a subsequent one-line priority patch; it is not used as unmodified source proof. [W3's independent review](../../package-native-review/W3-public-runtime-r1/REVIEW.md) verifies all 13,847 archived source rows and the exact license bytes.

Export and package manifests record both identities. Package-only operation requires a new export manifest containing that selection, checks binary bytes before version probes, and rejects a changed exporter, runtime, provenance, or contradictory version. Final guards rehash both identities after export/packaging. The copied Linux executable is checked against the selected runtime before ZIP creation. Existing PCK, font, source, and native-contract guards remain in place.

Only the Linux override receives `NOTICE/GODOT-RUNTIME.txt`, `GODOT-RUNTIME-PROVENANCE.json`, and original build/source verification records. Its START-HERE identifies the public template runtime and the separate official exporter. Existing MIT and COPYRIGHT bytes already match the public source and are preserved. Windows retains its existing executable, provenance, launcher and README.

Validation: [30 focused Python cases](runtime-cases.json), [14 existing UID cases](uid-regression.json), and [7 independent identity checks](independent-review.json) pass. The focused suite assembles real temporary ZIPs with tiny fixture PCKs, rejects wrong binaries/proof/version and copy mutation, and checks Linux-only notices and exporter-only font probes. Engine calls are mocked or blocked; these results do not qualify actual PCK export, gameplay, shader compilation, or a physical GPU. Setup runs the new focused test; the lead owns the corresponding workflow insertion. [Commands](commands.json) and exact tested sources are retained here.

## Next exact-source package operation

After the lead commits and remotely verifies this source successor, advance only the existing owned checkout at `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN` to that revision. Independently verify tracked/runtime bytes and the previously approved exact 113 non-runtime UID exclusions. Preserve both prior output roots and all official-package failure evidence. Use a fresh `/tmp/yuga-desktop-integrated-package-r3/build`; no source or runtime override is silently applied to an existing archive.

From the successor native project in that checkout, run the existing packager with both explicit identities:

```sh
taskset -c 0,1 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python3 tools/package-native.py \
  --linux-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --linux-runtime /workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-unmodified \
  --linux-runtime-provenance docs/evidence/desktop-finish/G0/template-baseline-r1/finished-build-verification.json \
  --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe \
  --build-dir /tmp/yuga-desktop-integrated-package-r3/build --export-only
```

Repeat those same arguments with `--package-only` after preserving the export log and source/cache/engine receipts. Rehash the two ZIPs and both manifests into a new SHA256SUMS, then hand W1 the exact source, archive, PCK, exporter/runtime identity and lane release. W1 must create a new preparation successor, extract the new archive, verify the dce payload separately from f64 export proof, and perform actual warm and fresh-state cold qualification. The old official f64 run is a retained blocked result, not acceptance of this new runtime.
