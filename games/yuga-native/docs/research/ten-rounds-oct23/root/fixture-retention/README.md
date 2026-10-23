# Exact preservation of inactive mutation fixtures

The 16 derived GLB mutation fixtures under
`/workspace/scratch/hero-family-independent-oct23` were preserved exactly in
a content-addressed archive, independently restored/compared, and then removed
from that inactive fixture directory. **Keep the archive.** It is the retained
copy of those actual test bytes, including eight meaningful original false
accepts; a generator recipe is not their replacement.

| Storage result | Bytes |
| --- | ---: |
| Original 16 GLBs removed | 576,799,244 |
| Original BIN payload total | 559,646,784 |
| Four distinct complete BIN payloads | 139,911,696 |
| Deduplicated block payloads, 63 objects | 53,084,832 |
| Retained TAR, including manifest/helper/headers | 53,237,760 |
| Source minus retained TAR | 523,561,484 |

After counting the additional retained manifest, recovery helpers and verification
receipts as well, the net logical reduction remains about **499 MiB**. Exact
all-overhead logical/allocated totals are in [cleanup-summary.json](cleanup-summary.json).

The archive is scratch only:

```text
/workspace/scratch/fixture-preservation-oct23/hero-family-independent-db1e3291.tar
SHA-256: 0aa1d6c00c35aa447fe5a890fa71d73e72c4f354d1d0f54064f33ced0a11f185
```

Raw GLB container headers, chunk headers, JSON padding and payload bytes are
retained. Each chunk's payload is split into exact 1 MiB content-addressed
blocks, which deduplicate repeated BIN data and unchanged portions of the
few binary mutations. Nothing is decoded/reencoded, normalized or regenerated.
The TAR also contains `manifest.json`, `restore.py` and a short standalone
README. It is uncompressed and uses only the Python standard library to restore.

Restore all original relative paths into a **fresh** directory:

```sh
python3 games/yuga-native/docs/research/ten-rounds-oct23/root/fixture-retention/restore.py \
  --archive /workspace/scratch/fixture-preservation-oct23/hero-family-independent-db1e3291.tar \
  --output /workspace/scratch/hero-family-restored-oct23
```

Optional `--only r1/mesh-unskinned.glb` restores one exact retained fixture.
The helper refuses an existing output directory, unsafe paths, invalid object
hashes, chunk mismatches or full-file mismatches. The original fixture directory
still contains its 24 logs/reports/other non-GLB files, so restore into a fresh
location and provide those restored file paths to a future test. Original
absolute paths remain in the historical reports; their bytes were not edited.

Safety and verification evidence:

- [Remote source confirmation](source-remote-confirmation.json): configured
  read-only `git ls-remote` returned
  `db1e3291abd78ec3fb8bf8496e3d098dd597150c` for
  `game/yuga-native-production`, matching local source-C HEAD. No credential
  file or token was read.
- [Inactive-process check](inactive-process-check.json): no process cwd or
  open file descriptor pointed into the fixture directory. The check was
  repeated immediately before removal; the parent confirmed the QA owner
  had finished.
- [Archive manifest](archive-manifest.json): enumerates every exact original
  relative path, full-file hash/size, raw container/chunk headers, chunk hashes
  and content-addressed blocks. Capture inode/mtime records were checked again
  before unlink.
- [Readback verification](readback-verification.json): all 16 files restored
  through `restore.py`, plus a separately written direct TAR-member
  concatenation, matched every original byte. All eight original false-accept
  fixture hashes are explicitly bound. This was completed before removal.
- [Cleanup summary](cleanup-summary.json): lists only the 16 removed GLBs,
  retained archive identity, measured allocated/logical sizes and unchanged
  non-GLB hashes. Temporary verification readbacks were also removed after
  comparison; the exact archive remains.

Only singly linked regular mutation-fixture `.glb` files in that one reviewed
directory were removed. Unique art, original assets/sources, `.blend` files,
logs, reports, model caches and all other worker paths were left intact. There
were no renders, package installs, Git edits or commits in this storage task.
The packer itself never deletes input files; deletion occurred only after the
separate exact-readback proof and final source/process rechecks.

The archive is cloud-local and is not pushed or remotely published. The small manifest, recovery helper and
evidence in this directory are the reviewable handoff. This TAR must remain
classified as required retained evidence in subsequent cloud-storage cleanup.
The repository alone cannot restore these fixtures without that retained TAR.
