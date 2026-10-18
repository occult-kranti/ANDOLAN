#!/usr/bin/env python3
"""Offline rest-space triangle differential probe; never rewrites a GLB.

Face-normal construction is adapted from Godot 4.6.3 Plane/SurfaceTool,
MIT, see NOTICE.md. Other diagnostic code is original, under the same MIT terms.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

KINDS = {"Cobalt handwoven silk": "cloth", "Cobalt lotus brocade": "cloth",
         "Worked warm gold": "cloth", "Swept black hair": "hair"}
LIMITS = {"cloth": .075, "hair": .018}


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def unit(v):
    length = math.sqrt(dot(v, v))
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError("degenerate differential")
    return tuple(x/length for x in v)


def face_normal(points):
    # Godot Plane counterclockwise branch; glTF has CCW front faces.
    return unit(cross(sub(points[0], points[1]), sub(points[0], points[2])))


def displaced(points, masks, offset):
    if len(points) != 3 or len(masks) != 3:
        raise ValueError("three points and masks required")
    if any(not math.isfinite(x) for p in points for x in p):
        raise ValueError("nonfinite position")
    if any(not math.isfinite(x) or x < 0 or x > 1 for x in masks):
        raise ValueError("invalid alpha mask")
    if len(offset) != 3 or any(not math.isfinite(x) for x in offset):
        raise ValueError("invalid offset")
    return [tuple(p[j]+offset[j]*w*w for j in range(3)) for p, w in zip(points, masks)]


def uv_frame(points, uvs):
    """Exact affine-triangle UV derivatives, including mirrored handedness."""
    e1, e2 = sub(points[1], points[0]), sub(points[2], points[0])
    d1, d2 = sub(uvs[1], uvs[0]), sub(uvs[2], uvs[0])
    det = d1[0]*d2[1]-d1[1]*d2[0]
    if abs(det) <= 1e-12:
        raise ValueError("degenerate UV")
    du = tuple((e1[j]*d2[1]-e2[j]*d1[1])/det for j in range(3))
    dv = tuple((-e1[j]*d2[0]+e2[j]*d1[0])/det for j in range(3))
    n = face_normal(points)
    t = unit(tuple(du[j]-n[j]*dot(n, du) for j in range(3)))
    handedness = 1 if dot(cross(n, t), dv) >= 0 else -1
    b = tuple(x*handedness for x in cross(n, t))
    return n, t, b, handedness


def angle(a, b):
    return math.degrees(math.acos(max(-1, min(1, dot(a, b)))))


def read_glb(path):
    raw = Path(path).read_bytes()
    if len(raw) < 20 or len(raw) > 64*1024*1024:
        raise ValueError("GLB size outside supported range")
    magic, version, length = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or length != len(raw):
        raise ValueError("invalid GLB header")
    chunks, cursor = {}, 12
    while cursor < length:
        size, kind = struct.unpack_from('<II', raw, cursor)
        cursor += 8
        if cursor+size > length or kind in chunks:
            raise ValueError("invalid GLB chunks")
        chunks[kind] = raw[cursor:cursor+size]
        cursor += size
    doc = json.loads(chunks[0x4e4f534a])
    blob = chunks[0x004e4942]
    if any('uri' in b for b in doc['buffers']) or len(doc['buffers']) != 1:
        raise ValueError("only one embedded buffer supported")
    return doc, blob, hashlib.sha256(raw).hexdigest()


def accessor(doc, blob, index):
    a = doc['accessors'][index]
    if 'sparse' in a or 'bufferView' not in a:
        raise ValueError("sparse or absent accessor buffer unsupported")
    formats = {5121: ('B', 1, 255), 5123: ('H', 2, 65535), 5125: ('I', 4, None), 5126: ('f', 4, None)}
    fmt, width, divisor = formats[a['componentType']]
    count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    view = doc['bufferViews'][a['bufferView']]
    if view.get('buffer', 0) != 0 or 'extensions' in view:
        raise ValueError("external/compressed buffer view unsupported")
    offset = view.get('byteOffset', 0)+a.get('byteOffset', 0)
    stride = view.get('byteStride', width*count)
    end = offset+(a['count']-1)*stride+width*count
    if stride < width*count or end > view.get('byteOffset', 0)+view['byteLength'] or end > len(blob):
        raise ValueError("accessor bounds")
    rows = [struct.unpack_from('<'+fmt*count, blob, offset+i*stride) for i in range(a['count'])]
    if a.get('normalized'):
        if divisor is None:
            raise ValueError("unsupported normalized component")
        rows = [tuple(v/divisor for v in row) for row in rows]
    if any(not math.isfinite(x) for row in rows for x in row):
        raise ValueError("nonfinite accessor")
    return rows


def audit(path):
    doc, blob, sha = read_glb(path)
    reports = []
    for mi, mesh in enumerate(doc['meshes']):
        for pi, primitive in enumerate(mesh['primitives']):
            name = doc['materials'][primitive['material']].get('name', '')
            if name not in KINDS:
                continue
            if primitive.get('mode', 4) != 4 or 'extensions' in primitive:
                raise ValueError("only uncompressed triangles supported")
            a = primitive['attributes']
            points, colors = accessor(doc, blob, a['POSITION']), accessor(doc, blob, a['COLOR_0'])
            if len(points) != len(colors) or any(len(c) != 4 or not 0 <= c[3] <= 1 for c in colors):
                raise ValueError("invalid semantic COLOR_0")
            indices = [x[0] for x in accessor(doc, blob, primitive['indices'])] if 'indices' in primitive else list(range(len(points)))
            if len(indices) % 3 or any(i < 0 or i >= len(points) for i in indices):
                raise ValueError("invalid triangle indices")
            kind, masks = KINDS[name], [c[3] for c in colors]
            offsets = [tuple(sign*LIMITS[kind] if j == axis else 0 for j in range(3)) for axis in range(3) for sign in [-1, 1]]
            turns, base_degenerate, changed_degenerate, active = [], 0, 0, 0
            for start in range(0, len(indices), 3):
                ids = indices[start:start+3]
                p, w = [points[i] for i in ids], [masks[i] for i in ids]
                try:
                    before = face_normal(p)
                except ValueError:
                    base_degenerate += 1
                    continue
                if max(w)-min(w) < 1e-12:
                    continue
                active += 1
                for off in offsets:
                    try:
                        turns.append(angle(before, face_normal(displaced(p, w, off))))
                    except ValueError:
                        changed_degenerate += 1
            turns.sort()
            reports.append({'mesh': mi, 'primitive': pi, 'material': name, 'kind': kind,
                'vertices': len(points), 'triangles': len(indices)//3, 'varying_mask_triangles': active,
                'zero_mask_vertices': sum(w == 0 for w in masks),
                'baseline_degenerate_triangles': base_degenerate, 'deformed_degenerate_samples': changed_degenerate,
                'max_face_normal_turn_degrees': turns[-1] if turns else 0,
                'p95_face_normal_turn_degrees': turns[int(.95*(len(turns)-1))] if turns else 0,
                'samples_above_90_degrees': sum(v > 90 for v in turns), 'samples': len(turns)})
    if not reports:
        raise ValueError("no admitted secondary materials")
    return {'schema': 1, 'input_sha256': sha, 'input': str(Path(path).resolve()), 'primitive_reports': reports,
        'scope': 'Rest mesh-local six-axis limit stress. Triangle geometry normals only; no skinning, GPU, smooth vertex-normal, collision, visual-quality or sphere-maximum claim.',
        'offset_limits_m': LIMITS, 'runtime_or_asset_written': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(audit(args.glb), indent=2)+'\n'
    if args.output:
        with args.output.open('x') as f:
            f.write(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
