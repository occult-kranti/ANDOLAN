#!/usr/bin/env python3
"""Original, smooth periodic roughness bake. No GLB, source texture or runtime writes."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SIZE = 1024
OUTPUT = HERE / 'textures/woven-roughness-r3.png'
PROFILE = {
    'schema': 1, 'task': 'R3-01', 'candidate': 'smooth-woven-roughness-r1',
    'texture': 'art/visual-rounds/cloth/textures/woven-roughness-r3.png',
    'dimensions': [SIZE, SIZE], 'png_encoding': '8-bit grayscale; one scalar channel',
    'color_space': 'linear data, not source_color / sRGB',
    'channel': 'RED', 'roughness_multiplier': 1.0,
    'rough_channel': [1.0, 0.0, 0.0, 0.0], 'use_rough_texture': True,
    'filter': 'linear_mipmap', 'repeat': True, 'mipmaps_generate': True,
    'preserve_specular_value': 0.38,
    'allowed_surface_names': ['Cobalt handwoven silk', 'Cobalt lotus brocade'],
    'lod_policy': 'Near/mid/far must share the same imported texture resource; identity UV transform on every LOD.',
    'binding_owner': 'Existing rama_surface_finish.gd woven map slot; root owns integration.',
    'recipe': {'mean': 0.79, 'warp_periods': 128, 'weft_periods': 96,
               'warp_amplitude': 0.010, 'weft_amplitude': 0.008,
               'crossing_amplitude': 0.006, 'supersampling_per_axis': 2},
    'preserved': ['original albedo', 'normal maps and strength', 'metallic',
                  'specular', 'mesh positions', 'UVs', 'rig', 'clips', 'vertex alpha',
                  'trim material', 'secondary offset', 'draw culling'],
    'art_gate': 'PENDING matched day/night front/rear/profile/gameplay plus continuous actions; no promotion implied.',
}


def field(u, v):
    """Continuous periodic crowns; no floor, random seed, step or authored image input."""
    warp = np.cos(2.0 * np.pi * 128 * u)
    weft = np.cos(2.0 * np.pi * 96 * v)
    crossing = np.cos(np.pi * 128 * u) * np.cos(np.pi * 96 * v)
    return 0.79 + 0.010 * warp + 0.008 * weft + 0.006 * crossing


def pixels(size=SIZE):
    # Average four subpixel samples before quantization; does not replace runtime mips.
    y, x = np.mgrid[:size, :size]
    value = np.zeros((size, size), dtype=np.float64)
    for dx in (0.25, 0.75):
        for dy in (0.25, 0.75):
            value += field((x + dx) / size, (y + dy) / size) * 0.25
    return np.rint(np.clip(value, 0.0, 1.0) * 255).astype(np.uint8)


def encode(a):
    stream = io.BytesIO()
    Image.fromarray(a).save(stream, format='PNG', optimize=False, compress_level=9)
    return stream.getvalue()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = encode(pixels())
    profile_data = (json.dumps(PROFILE, indent=2) + '\n').encode()
    products = [(OUTPUT, data), (HERE / 'material-profile.json', profile_data)]
    if args.check:
        for path, expected in products:
            if not path.exists() or path.read_bytes() != expected:
                raise SystemExit(f'Generated artifact differs: {path}')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        for path, value in products:
            path.write_bytes(value)
    print(json.dumps({'check': args.check, 'texture': str(OUTPUT), 'sha256': sha(data),
                      'bytes': len(data), 'min': int(pixels().min()), 'max': int(pixels().max())}))

if __name__ == '__main__':
    main()
