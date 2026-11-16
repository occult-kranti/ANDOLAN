# Final independent audit — R4

**R4 passes all 68 fresh independent checks** and supersedes R2 for delivery. The [original R2 reports](../README.md) remain untouched. [R4 receipt](receipt.json) records exact commands and evidence/tool/engine hashes.

| Group | Checks | Evidence |
| --- | ---: | --- |
| All frozen runtime/contract inputs and actual PCK payloads | 32 passed | [PCK/source report](pck-source-audit.json) |
| Both actual ZIP CRCs, complete payload hashes/manifest closure, runtime/PCK identity and notices | 27 passed | [ZIP report](zip-audit.json) |
| Actual packed compiled content10 validator and transactional old9 rejection | 9 passed | [Packed probe](packed-contract-probe.json), [log](packed-contract-probe.log) |

Frozen source digest: `27c18c8e98eb242aeddb228b47ffeece7dd74de0f460867b96d9291c56017c6d`, covering 622 runtime source files. All 46 finite contract-proof inputs match the export/package manifests and remain identical to R2. [The independent R2→R4 comparison](r2-to-r4-delta.json) confirms exactly one changed source: `scripts/native_field_shop_panel.gd`. The only changed payload in either PCK is its compiled `scripts/native_field_shop_panel.gdc`. Authority, Sangam and art sources remain unchanged.

Both platform PCKs are **88,199,444 bytes, 612 entries**, SHA256 `e4e860fc4014f22ef8d67e38df73309c67d5445f6b1221ec625b59480594c8bb`. Every member's stored MD5 and independently calculated SHA256 match the export directory. Direct packed catalogue/map/shop/shader bytes match frozen source. Actual compiled validator execution reports native content10, browser/proposal content1, content digest `c46efd90482a936b0220e4805edfbe7301c034cbfcf0545a066b3995c62f4e4b` and rules digest `aa4fba5258ed00f20fe6d4bce560ce298d7e7e025a336a73f4250635af478b2f`. Old9 admission/replay and a forged current descriptor with its stale digest reject transactionally. The pure headless probe exits0 with no engine warnings/errors.

| Final archive | Bytes | SHA256 | Members |
| --- | ---: | --- | ---: |
| [Linux ZIP](/workspaces/scratch/yuga-video-frozen-r1/build-r4/yuga-native-linux-x86_64.zip) | 115,178,949 | `b49421501197edf225e9edcf2c2d229ced777c52d53aa33646139df428de998a` | 51 |
| [Windows ZIP](/workspaces/scratch/yuga-video-frozen-r1/build-r4/yuga-native-windows-x86_64.zip) | 163,475,846 | `50b4a974b8762cad3137c44ea109cee0fd646c6bc286b0eb407a0c61c80a16c4` | 40 |

Every actual ZIP member passes CRC and SHA256/size comparison; entry sets exactly match manifest payloads plus the manifest itself, without duplicate/unsafe/encrypted/symlink paths. Runtime identity, Linux executable modes, required notices, frozen source state and contract-proof closure match. The archives and PCKs remain unchanged during this audit.

This is an isolated frozen-snapshot artifact audit, not a writeback into the concurrently edited shared checkout. The earlier live Sangam mismatch failures and superseded R2/R3 package checkpoints remain preserved. These 68 checks were rerun on R4; old content9 test counts are not included or relabelled as actual content10 package evidence.

No imports, exports, scene rendering, OS-window gameplay input or Windows execution were performed by this lane. The packed probe loads only the RefCounted contract/catalog. The receipt/footer and first-open layout fixes still require the separate rendered/input receipts; archive integrity does not establish UI quality or a complete production game. Root owns those acceptances and any release/publication decision.
