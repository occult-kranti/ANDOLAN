# Successor public audit preparation

Public audit **unrun**. No GitHub API, remote tag query, download, upload, publication or engine execution occurred during preparation. Root publication signal and the new root-confirmed draft/release ID remain required; actual warm/cold qualification belongs to W1.

The self-contained `reference.json` pins source `79e5c15d8a3657e16fda67acb277b2406120dcd1`, tag `yuga-desktop-polish-2026-10-18`, all five qualified assets and every ZIP member. Its source is W6's exact 40/40 qualification receipt SHA256 `e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400`. The new release ID is deliberately unset. Earlier r4 evidence informs the verifier's method; none of its public bytes/results is counted as successor evidence.

| Qualified asset | Bytes | SHA256 |
| --- | ---: | --- |
| `native-export-manifest.json` | 465170 | `104fbfd1c1f83616d5f1d55bcfe33903457b2241a4753117dbd366978f8c0e48` |
| `native-package-manifest.json` | 15546 | `8a74ef1abd3b29ddc86a72a162b07fbb41f4528a426f4f652c2a024b3d399527` |
| `SHA256SUMS.txt` | 381 | `026555b126ee4d6035f4ad7a920107a4e864f118399d699e6e705059891f75a5` |
| `yuga-native-linux-x86_64.zip` | 97903966 | `781d904d2f6986f423274cf23ecdc16a35df65df755db5171a97a152a3c88aa8` |
| `yuga-native-windows-x86_64.zip` | 146200829 | `8051586f45275c0e1956749f428a8ad2643ada69582410056597ed6f5efe01c8` |

`audit_public.py` defaults to a plan with zero network calls. Execution additionally requires both explicit execution/publication flags, the exact caller-supplied tag and full source, and root's positive new release ID. It rejects the earlier release ID 416367666. The public API must identify that exact published release, source and complete five-asset set, including digests, sizes and URLs. The public Git tag is resolved independently. Each file is freshly downloaded through normal verified HTTPS, retained, counted and streamed through SHA256; downloaded checksums must cover the other four files exactly.

ZIP checks stream every member to EOF for CRC, byte count and SHA256; require the independent qualified member inventory, canonical unique regular unencrypted members, declared payloads, source/platform/exporter identity and executable modes. Linux's declared patched runtime, eleven exact source/build/license proofs and official exporter remain distinct; Windows's separately pinned official engine remains explicit. The common 70,594,852-byte PCK SHA256 is `f2be4e20a0f3ea3915c5ab94e3896278ab4778991e80c6c8abaadc5209511a59`. Its 550-entry directory is parsed once in memory for path uniqueness, bounds, stored MD5 and per-entry SHA256. Windows independently streams and matches the complete PCK member; reuse of the first directory proof requires identical full exported entry tables and whole-file bytes. No files are extracted.

All five downloads, including both ZIPs, remain under a fresh `/workspace/scratch` output until separately authorized safe cleanup. The helper contains no deletion path. Initial fresh free space must be at least 785,651,108 bytes: 244,585,892 retained asset bytes, a 500 MiB floor and 16 MiB metadata allowance. It checks that floor again before and after each download. A partial or failed audit remains available for diagnosis; use a fresh directory for a later run.

Preparation checks in `preparation-checks.json` pass: Python syntax, default plan, twelve in-memory caller/path/PCK checks, missing-publication rejection and exact hashes/schema of the three small local qualified metadata files. The process/network route was blocked during these checks and was never called. No full ZIP or PCK payload rehearsal was run in this preparation.

After root's publication signal and fresh storage check, run from `/workspace/ANDOLAN`, substituting the new numeric ID from root for `NEW_RELEASE_ID`:

```sh
taskset -c 4 python3 -B games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W3-public-audit-r1/audit_public.py \
  --execute-public-download --root-publication-signal \
  --expected-tag yuga-desktop-polish-2026-10-18 \
  --expected-source 79e5c15d8a3657e16fda67acb277b2406120dcd1 \
  --expected-release-id NEW_RELEASE_ID \
  --output /workspace/scratch/yuga-continuation-W3-public-audit-r1
```

A later pass binds independent public bytes to the separately qualified package. It does not rerun gameplay, execute Windows, establish physical GPU performance or accept finished art. The current cloud discovery packet, source, caches and Git metadata remain unchanged.
