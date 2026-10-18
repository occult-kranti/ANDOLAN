# Independent public r4 download audit

**Passed.** Fresh public downloads of all five assets match the published API digests/sizes, the sealed qualified r4 pins, and downloaded SHA256SUMS. Release 416367666 became public at 2026-10-18T11:17:53Z. Independent public Git tag resolution confirms `yuga-desktop-finish-2026-10-18` points to exact source `96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12`.

| Asset | Bytes | SHA256 |
| --- | ---: | --- |
| native-export-manifest.json | 456710 | `4cb3316300092dcdb99016f3c0e6f024066df2f94999a3b7b4944247870aa4a7` |
| native-package-manifest.json | 14741 | `01581b3d740097aa61bd35c3722a85dca1021dddb1766a2a28e1c1b53645417c` |
| SHA256SUMS.txt | 381 | `63c7e06548e879aa2848bb56cbf0a9ccada77fca6a1978b2918dbe939f5549d3` |
| yuga-native-linux-x86_64.zip | 97835664 | `27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e` |
| yuga-native-windows-x86_64.zip | 146132535 | `34d8c19d30f7cafe6ad56247c2524d09c15f307cc0cde20572a56eb3d29b1fc6` |

Linux has 45 unique canonical regular ZIP members; Windows has 34. Every member was streamed through EOF for CRC checking and compared with its declared size/SHA256. Both complete PCKs have 543 independently checked directory entries with bounded offsets, canonical unique paths, stored MD5 and expected size/SHA256. Their identical complete PCK hash is `b84ac0f4f1e70fbfc5366234729a9e97012e5664bd6a3a43bfb77fe61e7b6903`.

The Linux archive contains the explicitly declared one-patch `pipeline-low-priority-v1` runtime e69, the distinct official f64 exporter provenance, and all 11 exact source/build/license proof files. Windows contains its separately pinned official engine and remains unexecuted. The exact downloaded export and package manifests retain all source and runtime identities; the machine receipt records per-member results and each download/API/tag command.

The previously sealed audit script ran unchanged once. All outputs first went to `/workspace/scratch/yuga-desktop-r4-public-audit-r1`; this packet preserves byte-exact small metadata, progress record and final verification. Only one newly downloaded ZIP was stored at a time; each was removed after full verification. No expanded payload copies, import, engine, renderer, Git mutation, upload or publication occurred in this audit.

This connects publicly downloaded bytes to the separately qualified exact package. It does not claim a new downloaded-build gameplay run, Windows execution, physical GPU performance, listening quality, native online play or finished commercial art. Root owns the separate overall release review; W1 owns actual warm/cold execution evidence.
