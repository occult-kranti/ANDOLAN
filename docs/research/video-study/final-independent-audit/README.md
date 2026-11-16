# FINAL-INDEPENDENT-AUDIT-01

**The actual frozen Linux and Windows packages pass this independent integrity and contract audit: 68 checks.** This is archive/source/PCK/admission evidence, not rendered gameplay, full-game completion, physical-GPU performance or Windows execution.

The audited source is the isolated `/workspaces/scratch/yuga-video-frozen-r1` snapshot. Its candidate overlay regenerates the original Sangam district with that snapshot's frozen authoring/shader inputs and updates its two copied map source pins. No snapshot changes were written back to the shared checkout. The earlier live-tree stable shader/specification failures remain preserved under `../integration-qa/content10-review/`; they are not relabelled as passing. Frozen source identity, rather than the baseline Git commit alone, identifies this build's uncommitted changes.

| Check group | Result | Evidence |
| --- | ---: | --- |
| Source state, contract closure and both actual PCK directories/payloads | 32 passed | [PCK/source audit](pck-source-audit.json) |
| Both actual ZIPs: CRC, payload hashes, manifest closure, PCK/runtime identities and notices | 27 passed | [ZIP audit](zip-audit.json) |
| Actual PCK compiled contract/catalog: effective content10 and transactional rejection of old identities | 9 passed | [Packed contract probe](packed-contract-probe.json), [log](packed-contract-probe.log) |

[The audit receipt](receipt.json) records exact commands, tool/engine hashes and report hashes. The independent Python readers do not invoke the package builder. They stream actual archive entries and read the PCK directory themselves; every PCK member's stored MD5 and independently calculated SHA256 were verified. The pure headless Godot probe loads only the packed `native_contracts.gd` resource/catalog and exercises its RefCounted validator. It does not load a world scene or import/render assets.

The frozen source-state aggregate is `e50681013171d1a503c29726ee76a80b9b5b7e85375b110d9e606f1d25cb343f`: **622 runtime source files, 216,802,867 bytes**, all independently rehashed and equal to the export manifest. All **46 finite contract-proof inputs** match the same snapshot. Effective native content10 has nineteen source pins and retains all seventeen content9 pins. The canonical content-source digest, packed catalogue, Sangam specification, finish shader and shop catalogue match their exact frozen source payloads.

Both platforms contain the same **88,199,188-byte, 612-entry PCK**, SHA256 `ef299abef23c5ad7a406508f34627725e793c6d097b79d773a8cddc103fce5b9`. The actual PCK compiled validator reports:

- Native content revision **10**; browser/proposal remain content1 and their original protocol/state.
- Content digest `c46efd90482a936b0220e4805edfbe7301c034cbfcf0545a066b3995c62f4e4b`.
- Rules digest `aa4fba5258ed00f20fe6d4bce560ce298d7e7e025a336a73f4250635af478b2f`.
- Native base-map digest `d39043bfaabd9c3e173f03d68423269b5308b60c6906968315405690f844d77c`.

Old content9 admission/replay and a content10 descriptor carrying a stale content digest reject without changing the active validator state. A matching current descriptor opens a validator session only; it does not establish a network connection. The packed probe exits0 with no engine warning/error diagnostics. Compiled GDScript payload identity is independently matched against the export directory; this is not a decompilation claim or proof that a source hash alone establishes semantic equivalence.

| Actual archive | Bytes | SHA256 | Members |
| --- | ---: | --- | ---: |
| [Linux ZIP](/workspaces/scratch/yuga-video-frozen-r1/build-r2/yuga-native-linux-x86_64.zip) | 115,178,667 | `d0d11fb5d4e1d64354a5bd49ff7bf6fba09c0923f0729017df645f6d3a52fbd6` | 51 |
| [Windows ZIP](/workspaces/scratch/yuga-video-frozen-r1/build-r2/yuga-native-windows-x86_64.zip) | 163,475,561 | `ffdcce305d3c4e49c2259002c691a088a2c2b97924d205f4ea3ad9f266d5364c` | 40 |

For each ZIP, every member is unique, canonical, unencrypted and not a symlink; the complete entry set equals `PACKAGE-MANIFEST.json`'s payload closure plus the manifest itself. Every declared payload byte count/SHA256 matches actual decompressed bytes. PCK payloads match the standalone audited PCKs. The included runtime matches the package's declared runtime identity. Linux launcher/runtime executable modes are retained, and required engine, asset and project notices exist as actual ZIP payloads. Both archives remain unchanged through the audit.

No imports, exports, Blender jobs, scene renders, OS-window gameplay input or live online matches were performed by this audit. Identical Windows PCK data does not qualify Windows execution. The snapshot build owner's separate 83 source checks, 33 map checks and 21 shop checks have their own receipts; old content9 tests are not counted among these 68 checks or substituted for actual content10 package evidence. Root owns rendered/input acceptance, preservation of the overlay, and any release/publication decision.
