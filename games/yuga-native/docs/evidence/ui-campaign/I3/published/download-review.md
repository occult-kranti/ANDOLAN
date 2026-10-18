# Independent public-download verification

**Passed.** Fresh downloads of all five assets from the public [YUGA native UI release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18) match their public API sizes/digests. The four build files also match the actual qualified package-r3 files and the downloaded `SHA256SUMS.txt`. Release 416177473 is non-draft, marked prerelease, and was published at `2026-10-18T02:10:32Z`. Independent `git ls-remote` resolves its tag to `9e81a7c849837dea477ddb5a8c93f43665774573`, matching the release target and manifests.

| Download | Bytes | SHA-256 |
| --- | ---: | --- |
| native-export-manifest.json | 397267 | `9b181f1c67e32de6481cd9256c61b38eb54de6ce2afe54e05f2a68ae2931d75b` |
| native-package-manifest.json | 12765 | `12010a4eae0b6645d946e5aaa8b52daba5f8f233425356aa942891ab0b87c1b2` |
| SHA256SUMS.txt | 381 | `971400864643f5e02c90248b3b3429f3535bf424db94c1f023c53a9551eed2a1` |
| yuga-native-linux-x86_64.zip | 137812335 | `56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5` |
| yuga-native-windows-x86_64.zip | 145813678 | `16f6e210fef90f26c1c725e503805fb5e9c4ee76d64e86cb2ff7b0788ea186c5` |

Both ZIPs contain exactly 29 unique canonical members. Every member CRC and all 28 declared payload sizes/SHA-256 hashes pass on each platform, including the bundled engines and PCK. Both embedded manifests match the public export source records. Each PCK independently passes all 519 directory/payload bounds, sizes, SHA-256 and stored MD5 checks and has the qualified SHA `d387d34ad37fc959f974b9ced0107d5ad2a0e2505e55a090dd20fc583d62aa27`.

[Machine-readable receipt](download-verification.json) records 8/8 grouped release/download checks, 9/9 archive predicates for each platform, public asset IDs/URLs, exact commands and per-member results. Downloads used direct public release URLs with normal TLS verification. The five files total 284,036,426 bytes and are retained in `/tmp/yuga-ui-public-downloads`; no additional expanded archive copies were written.

No engine was started, and no import, rendering or full source audit was repeated. Public byte identity connects the Linux download to the previously reviewed exact local package, including its two first-run native recoveries and visual limits. This audit does not claim a new downloaded-build gameplay run. **Windows remains unexecuted**; its result is archive and payload integrity only. Hardware performance, audio listening, online gameplay and final art quality remain outside this verification.
