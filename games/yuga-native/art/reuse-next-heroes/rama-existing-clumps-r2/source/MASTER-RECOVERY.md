# Exact editable master recovery

The existing saved master is preserved as [`rama-existing-nape-clumps.blend.gz`](rama-existing-nape-clumps.blend.gz). It was streamed into gzip with an empty filename header, compression level 6 and mtime 0; no Blender regeneration, render or source alteration occurred.

- Archive: **27,803,879 bytes (26.52 MiB)**; SHA-256 `b19cf43c7065139c2a835deb1f49574f7d6a7c1e61d21f68577c2e559b4d5a98`.
- Exact decompressed master: **77,441,473 bytes**; SHA-256 `12af67abe3f301647619a41a32198de091e6d98ee2fe9528dcd7266021f2c808`.
- Both the streamed decompression hash and unchanged original hash were verified. [Compression receipt](master-archive-receipt.json).

Recover outside the checkout into a fresh filename. The following command refuses to overwrite an existing file and verifies both the archive and decompressed bytes. Run from this packet directory:

```sh
python3 - source/rama-existing-nape-clumps.blend.gz /workspace/scratch/recovered-w3/rama-existing-nape-clumps.blend <<'PY_RECOVER'
from pathlib import Path
import gzip, hashlib, sys
archive, destination = map(Path, sys.argv[1:])
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
assert sha(archive) == 'b19cf43c7065139c2a835deb1f49574f7d6a7c1e61d21f68577c2e559b4d5a98'
destination.parent.mkdir(parents=True, exist_ok=True)
h = hashlib.sha256()
with gzip.open(archive, 'rb') as source, destination.open('xb') as output:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        h.update(chunk)
        output.write(chunk)
assert destination.stat().st_size == 77441473
assert h.hexdigest() == '12af67abe3f301647619a41a32198de091e6d98ee2fe9528dcd7266021f2c808'
print(destination, h.hexdigest())
PY_RECOVER
```

The recovered master is byte-identical to the original saved scene. Its archival does not change the candidate phase or authorize runtime use. Preserve its original version, cameras, lights, modifiers and shape keys. Any new edits or captures need fresh outputs and their own receipts.

R2 retains the editable `W3 two unequal nape flow families` shape key, original basis and four named locked cameras. Root and W1 rejected runtime advancement. Do not export a GLB or substitute this scene into the game. If an authorized future diagnostic replay uses a recovered scene at another location, copy the source receipt and change only `scene.path` to that recovery location; retain `scene.sha256` and record the receipt-path adjustment. That replay is new evidence, not the existing eight-frame receipt.
