#!/usr/bin/env python3
"""Create an intentionally corrupted copy to verify the joint-index guard."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'hero-rama-lod'))
from glb_lod import GLB, DTYPES

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if args.source.resolve() == args.output.resolve():
    raise ValueError('Use a separate output, never overwrite the source')
x = GLB(args.source)
primitive = x.doc['meshes'][0]['primitives'][0]
accessor = x.doc['accessors'][primitive['attributes']['JOINTS_0']]
view = x.doc['bufferViews'][accessor['bufferView']]
dtype = DTYPES[accessor['componentType']]
if dtype.kind != 'u' or dtype.itemsize not in (1, 2):
    raise ValueError('Expected unsigned byte or unsigned short joint indices')
raw = bytearray(x.raw)
offset = 20 + struct.unpack_from('<I', raw, 12)[0] + 8 + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
old = int.from_bytes(raw[offset:offset + dtype.itemsize], 'little')
new = (old + 1) % len(x.doc['skins'][0]['joints'])
raw[offset:offset + dtype.itemsize] = new.to_bytes(dtype.itemsize, 'little')
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(raw)
print(f'Wrote separate negative control; first joint index {old} -> {new}')
