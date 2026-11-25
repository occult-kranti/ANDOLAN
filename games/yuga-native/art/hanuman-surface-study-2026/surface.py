"""Add a reversible rest-space-derived skin/fur surface pass to a pinned Hanuman GLB.

The donor GLB keeps its rig, topology, weights, vertex colors, and existing material
textures. Added tangent normals use the glTF normalTexture channel convention;
the original normal strength and metallic/roughness factors are retained.

    python3 surface.py --output /tmp/hanuman-surface.glb --maps /tmp/hanuman-maps

No external imagery is used. The existing YUGA surfacing code owns GLB I/O.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'hanuman-hero-finish/tools'))
from surfaces import accessor_values, read_gltf, write_gltf  # noqa: E402

CONFIG = json.loads((HERE / 'surface.json').read_text())
BODY = 'Vanara · painted copper anatomy'
PREFIX = 'YUGA surface study 2026 / '


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smooth(lo, hi, value):
    t = np.clip((value - lo) / (hi - lo), 0., 1.)
    return t * t * (3. - 2. * t)


def value_noise(x, y, z, seed):
    """Continuous, seeded 3D value noise; anisotropy comes from input scaling."""
    x0, y0, z0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32), np.floor(z).astype(np.int32)
    tx, ty, tz = smooth(0., 1., x - x0), smooth(0., 1., y - y0), smooth(0., 1., z - z0)

    def hashed(ix, iy, iz):
        h = ix.astype(np.uint32) * np.uint32(0x8da6b343)
        h ^= iy.astype(np.uint32) * np.uint32(0xd8163841)
        h ^= iz.astype(np.uint32) * np.uint32(0xcb1ab31f)
        h ^= np.uint32(seed)
        h ^= h >> np.uint32(16)
        h *= np.uint32(0x7feb352d)
        h ^= h >> np.uint32(15)
        h *= np.uint32(0x846ca68b)
        h ^= h >> np.uint32(16)
        return (h & np.uint32(0xffffff)).astype(np.float32) / 8388607.5 - 1.

    result = np.zeros_like(x, dtype=np.float32)
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                weight = (tx if i else 1. - tx) * (ty if j else 1. - ty) * (tz if k else 1. - tz)
                result += weight * hashed(x0 + i, y0 + j, z0 + k)
    return result


def original_image(doc, binary, index, size):
    tex = doc['textures'][index]
    image = doc['images'][tex['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    with Image.open(io.BytesIO(binary[start:start + view['byteLength']])) as file:
        return np.asarray(file.convert('RGB').resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32) / 255.


def raster_rest_positions(doc, binary, material, size):
    """Interpolate original positions into UV0 and conservatively reject overlap conflicts."""
    xyz = np.zeros((size, size, 3), dtype=np.float32)
    valid = np.zeros((size, size), dtype=bool)
    conflict = np.zeros((size, size), dtype=bool)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if prim.get('material') != material:
                continue
            attributes = prim['attributes']
            pos = accessor_values(doc, binary, attributes['POSITION']).astype(np.float32)
            uv = accessor_values(doc, binary, attributes['TEXCOORD_0']).astype(np.float32)
            faces = accessor_values(doc, binary, prim['indices']).reshape(-1, 3)
            for tri in faces:
                point = uv[tri] * (size - 1)
                x0, y0 = np.maximum(np.floor(point.min(0)).astype(int), 0)
                x1, y1 = np.minimum(np.ceil(point.max(0)).astype(int), size - 1)
                if x0 > x1 or y0 > y1:
                    continue
                x = np.arange(x0, x1 + 1, dtype=np.float32)[None, :]
                y = np.arange(y0, y1 + 1, dtype=np.float32)[:, None]
                (ax, ay), (bx, by), (cx, cy) = point
                den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
                if abs(den) < 1e-8:
                    continue
                u = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / den
                v = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / den
                w = 1. - u - v
                inside = (u >= -1e-4) & (v >= -1e-4) & (w >= -1e-4)
                if not inside.any():
                    continue
                result = u[..., None] * pos[tri[0]] + v[..., None] * pos[tri[1]] + w[..., None] * pos[tri[2]]
                window = xyz[y0:y1 + 1, x0:x1 + 1]
                used = valid[y0:y1 + 1, x0:x1 + 1]
                prior = window.copy()
                # Mirrored UV islands are compatible if abs(X), Y and Z agree.
                delta = result - prior
                delta[..., 0] = np.abs(result[..., 0]) - np.abs(prior[..., 0])
                conflict[y0:y1 + 1, x0:x1 + 1] |= inside & used & (np.linalg.norm(delta, axis=-1) > .02)
                window[inside & ~used] = result[inside & ~used]
                used |= inside
    return xyz, valid, conflict


def region_mask(xyz):
    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
    a = np.abs(x)
    # Values are artistic spatial envelopes around real rest-space body positions.
    arms = smooth(.24, .36, a) * (1. - smooth(.62, .73, a))
    arms *= smooth(1.12, 1.20, y) * (1. - smooth(1.58, 1.69, y))
    cheek = smooth(.055, .080, a) * (1. - smooth(.108, .135, a))
    cheek *= smooth(1.755, 1.79, y) * (1. - smooth(1.85, 1.88, y)) * smooth(.065, .13, z)
    return np.maximum(arms, .52 * cheek)


def append_png(doc, binary, name, data, sampler, maps):
    pixels = np.rint(np.clip(data, 0., 1.) * 255.).astype(np.uint8)
    out = io.BytesIO()
    Image.fromarray(pixels, 'RGB').save(out, format='PNG', compress_level=6)
    encoded = out.getvalue()
    if maps is not None:
        maps.mkdir(parents=True, exist_ok=True)
        (maps / (name + '.png')).write_bytes(encoded)
    binary.extend(b'\0' * ((-len(binary)) % 4))
    view = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(encoded)})
    binary.extend(encoded)
    image = len(doc['images'])
    doc['images'].append({'name': PREFIX + name, 'bufferView': view, 'mimeType': 'image/png'})
    texture = len(doc['textures'])
    doc['textures'].append({'source': image, 'sampler': sampler})
    return texture, hashlib.sha256(encoded).hexdigest()


def run(source: Path, output: Path, maps: Path | None, report: Path, config: Path):
    source = source.resolve(strict=True)
    output = output.resolve()
    if output == source:
        raise ValueError('Never overwrite the source model')
    if sha(source) not in CONFIG['source_sha256']:
        raise ValueError('Source model differs from the pinned facial candidates')
    doc, binary = read_gltf(source)
    if any(image.get('name', '').startswith(PREFIX) for image in doc['images']):
        raise ValueError('This surface pass has already been applied')
    mats = [i for i, item in enumerate(doc['materials']) if item.get('name') == BODY]
    if len(mats) != 1:
        raise ValueError('Expected one source body material')
    index = mats[0]
    material = doc['materials'][index]
    pbr = material['pbrMetallicRoughness']
    normal_texture = material['normalTexture']
    old_normal = normal_texture['index']
    old_rough = pbr['metallicRoughnessTexture']['index']
    if 'baseColorTexture' in pbr:
        raise ValueError('Source uses an unexpected body base-color map')
    sampler = doc['textures'][old_normal].get('sampler', 0)
    size = CONFIG['resolution']
    points, valid, overlap = raster_rest_positions(doc, binary, index, size)
    # Fill a narrow gutter from the nearest valid surface point for mip filtering.
    distance, nearest = ndimage.distance_transform_edt(~valid, return_indices=True)
    inside = valid | (distance <= CONFIG['padding_pixels'])
    points = points[tuple(nearest)]
    overlap = overlap[tuple(nearest)]
    mask = region_mask(points) * inside * ~overlap
    # Soften UV boundaries and avoid turning an overlap rejection into an abrupt edge.
    mask = ndimage.gaussian_filter(mask.astype(np.float32), .8) * inside
    x, y, z = points[..., 0], points[..., 1], points[..., 2]
    # Elongated fibers run roughly along the arm axis, modulated in 3D rather
    # than painted as a UV-grid pattern. The mask keeps most of the face clear.
    if CONFIG.get('fiber_mode') == 'anisotropic-value-noise':
        fiber = .7 * value_noise(43. * x, 205. * y, 205. * z, 173) + .3 * value_noise(83. * x, 310. * y, 310. * z, 421)
        pore = value_noise(310. * x, 310. * y, 310. * z, 911)
    else:
        frequency = CONFIG['fiber_period_per_m']
        phase = 2. * math.pi * (frequency * (.72 * y + .69 * z) + .7 * np.sin(26. * x + 15. * z))
        fiber = np.sin(phase) * (.52 + .48 * np.sin(54. * x - 18. * y + 12. * z))
        pore = np.sin(2. * math.pi * (121. * x + 94. * y)) * np.sin(2. * math.pi * (103. * z - 81. * y))
    height = mask * (CONFIG['fur_height_strength'] * fiber + CONFIG['pore_height_strength'] * pore)
    base = original_image(doc, binary, old_normal, size) * 2. - 1.
    dx = np.gradient(height, axis=1)
    dy = np.gradient(height, axis=0)
    base[..., 0] -= dx
    base[..., 1] += dy
    base /= np.maximum(np.linalg.norm(base, axis=-1, keepdims=True), 1e-8)
    normal_map = .5 + .5 * base
    rough = original_image(doc, binary, old_rough, size)
    rough[..., 1] = np.clip(rough[..., 1] + CONFIG['roughness_gain_max'] * mask * (.5 + .5 * fiber), 0., 1.)
    # White is neutral because it multiplies the existing linear vertex pigment.
    value = 1. - CONFIG['color_darkening_max'] * mask * (.5 + .5 * fiber)
    color = np.repeat(value[..., None], 3, axis=-1)
    normal_id, normal_sha = append_png(doc, binary, 'anatomy-normal-linear', normal_map, sampler, maps)
    rough_id, rough_sha = append_png(doc, binary, 'anatomy-metal-rough-linear', rough, sampler, maps)
    color_id, color_sha = append_png(doc, binary, 'anatomy-basecolor-srgb', color, sampler, maps)
    normal_texture['index'] = normal_id
    pbr['metallicRoughnessTexture']['index'] = rough_id
    pbr['baseColorTexture'] = {'index': color_id}
    write_gltf(output, doc, binary)
    data = {
        'source_sha256': sha(source), 'candidate_sha256': sha(output),
        'config_sha256': sha(config),
        'material': BODY, 'resolution': [size, size],
        'uv_pixels_covered': int(valid.sum()), 'uv_pixels_with_overlap_conflict': int((overlap & valid).sum()),
        'masked_pixels': int((mask > .01).sum()), 'max_mask': float(mask.max()),
        'normal_scale_preserved': normal_texture.get('scale', 1.),
        'texture_sha256': {'normal': normal_sha, 'metal_rough': rough_sha, 'base_color': color_sha},
        'source_and_weights': 'Existing YUGA model and built-in project textures; no third-party imagery.',
        'scope': 'Analytic texture study; not geometry fur, photographic skin or a runtime performance measurement.'
    }
    report.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    global CONFIG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=(HERE / 'surface.json'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--output', type=Path, default=(HERE / 'hanuman-surface-candidate.glb'))
    parser.add_argument('--maps', type=Path, default=(HERE / 'maps'))
    parser.add_argument('--report', type=Path, default=(HERE / 'surface-report.json'))
    args = parser.parse_args()
    CONFIG = json.loads(args.config.read_text())
    run(args.source or (HERE / CONFIG['source']), args.output, args.maps, args.report, args.config)


if __name__ == '__main__':
    main()
