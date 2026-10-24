# Exact editable master recovery

The existing saved master is preserved as [`approved-rama-hair-sculpt.blend.gz`](approved-rama-hair-sculpt.blend.gz). It was streamed into gzip with an empty filename header, compression level 6 and mtime 0; no Blender regeneration, render or source alteration occurred.

- Archive: **36,466,207 bytes (34.78 MiB)**; SHA-256 `d70201ac5cf3436fc06eef717f4ee9b3a3ced16be93e3dcfdc27ccbc4788a112`.
- Exact decompressed master: **122,214,321 bytes**; SHA-256 `30b44c964664a5326dc89576748e63649fa10d5cfe30878ff3aa103e5cdd53f6`.
- Both the streamed decompression hash and unchanged original hash were verified. [Compression receipt](master-archive-receipt.json).

Recover outside the checkout into a fresh filename. The following command refuses to overwrite an existing file and verifies both the archive and decompressed bytes. Run from this packet directory:

```sh
python3 - source/approved-rama-hair-sculpt.blend.gz /workspace/scratch/recovered-w3/approved-rama-hair-sculpt.blend <<'PY_RECOVER'
from pathlib import Path
import gzip, hashlib, sys
archive, destination = map(Path, sys.argv[1:])
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
assert sha(archive) == 'd70201ac5cf3436fc06eef717f4ee9b3a3ced16be93e3dcfdc27ccbc4788a112'
destination.parent.mkdir(parents=True, exist_ok=True)
h = hashlib.sha256()
with gzip.open(archive, 'rb') as source, destination.open('xb') as output:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        h.update(chunk)
        output.write(chunk)
assert destination.stat().st_size == 122214321
assert h.hexdigest() == '30b44c964664a5326dc89576748e63649fa10d5cfe30878ff3aa103e5cdd53f6'
print(destination, h.hexdigest())
PY_RECOVER
```

The recovered master is byte-identical to the original saved scene. Its archival does not change the candidate phase or authorize runtime use. Preserve its original version, cameras, lights, modifiers and shape keys. Any new edits or captures need fresh outputs and their own receipts.

R1 retains baseline and non-destructive lattice. The corrected r5 GLB remains a derived artifact: use the pinned `artist_r1/carry_exact_glb.py`, the exact canonical source GLB, this recovered master and a decompressed copy of `source/sculpt-receipt.json.gz`. Pass the recovered master through `--scene`; the carry verifies its hash independently of its filesystem location. Use Blender 4.3.2 and a fresh output directory. The expected r5 GLB SHA is `85c16967bdec0eeb6cf4c5b331fe07d236df114ebf3730937d97300e4dda0777`; verify it before reuse. Do not substitute a changed reconstruction or promote the candidate on archival proof alone.
