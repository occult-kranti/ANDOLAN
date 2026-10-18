#!/usr/bin/env python3
"""Original, closed three-vane fletching in the existing arrow's +Y frame."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROFILE = [(.0028, .050), (.0095, .063), (.01199, .092),
           (.010, .118), (.004, .137), (.0028, .137)]
THICKNESS = .0008


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(a):
    length = math.sqrt(dot(a, a))
    assert length > 1e-12
    return [x/length for x in a]


def build():
    vertices, normals, tangents, uvs, indices = [], [], [], [], []

    def triangle(a, b, c):
        e1, e2 = sub(b, a), sub(c, a)
        normal = unit(cross(e1, e2))
        tangent = unit(e1)
        sign = -1 if dot(cross(normal, tangent), e2) < 0 else 1
        for point, uv in zip((a, b, c), ((.46, .44), (.54, .44), (.46, .56))):
            indices.append(len(vertices))
            vertices.append([round(x, 10) for x in point])
            normals.append([round(x, 10) for x in normal])
            tangents.append([*[round(x, 10) for x in tangent], sign])
            uvs.append(list(uv))

    for vane in range(3):
        angle = 2*math.pi*vane/3
        radial = (math.cos(angle), 0, math.sin(angle))
        side = (-math.sin(angle), 0, math.cos(angle))
        rings = []
        for sign in (-1, 1):
            rings.append([[r*radial[0]+sign*THICKNESS*.5*side[0], y,
                           r*radial[2]+sign*THICKNESS*.5*side[2]] for r, y in PROFILE])
        back, front = rings
        for i in range(1, len(PROFILE)-1):
            triangle(front[0], front[i], front[i+1])
            triangle(back[0], back[i+1], back[i])
        for i in range(len(PROFILE)):
            j = (i+1) % len(PROFILE)
            triangle(front[i], back[i], back[j])
            triangle(front[i], back[j], front[j])
    return {
        'schema': 1, 'name': 'Original three-vane ivory arrow fletching',
        'generator': 'art/hero-finish/s3-arrow-fletching/build_fletching.py',
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'frame': 'Existing RamaMotion.NockedArrow local +Y; nock at origin; metres.',
        'source_contract': {'shaft_radius_m': .003, 'shaft_length_m': .72,
                            'tip_length_m': .065, 'new_transform_writers': 0},
        'profile_radial_axis_m': PROFILE, 'thickness_m': THICKNESS,
        'vanes': 3, 'triangles': len(indices)//3,
        'vertices': vertices, 'normals': normals, 'tangents': tangents,
        'uvs': uvs, 'indices': indices,
        'rights': 'Original authored YUGA geometry. No third-party model or image input.',
        'scope': 'Optional candidate only; no current rig, source GLB, shaft, tip or socket edits. Native appearance and action clearance require separate checks.',
    }


def validate(data):
    assert len(data['vertices']) == len(data['normals']) == len(data['tangents']) == len(data['uvs']) == 180
    assert data['triangles'] == 60 and data['indices'] == list(range(180))
    edges = {}
    minimum_area = math.inf
    for i, (p, n, t, uv) in enumerate(zip(data['vertices'], data['normals'], data['tangents'], data['uvs'])):
        assert all(math.isfinite(x) for x in p+n+t+uv)
        assert .049999 < p[1] < .137001 and math.hypot(p[0], p[2]) < .01201
        assert abs(dot(n, n)-1) < 1e-8 and abs(dot(t[:3], t[:3])-1) < 1e-8
        assert abs(dot(n, t[:3])) < 1e-8 and abs(t[3]) == 1
        assert all(0 <= x <= 1 for x in uv)
    for i in range(0, 180, 3):
        points = data['vertices'][i:i+3]
        area2 = cross(sub(points[1], points[0]), sub(points[2], points[0]))
        area = math.sqrt(dot(area2, area2))*.5
        assert area > 1e-10 and dot(area2, data['normals'][i]) > 0
        minimum_area = min(minimum_area, area)
        for a, b in zip(points, points[1:]+points[:1]):
            key = tuple(sorted((tuple(a), tuple(b))))
            edges[key] = edges.get(key, 0)+1
    assert all(count == 2 for count in edges.values()), 'open or nonmanifold vane'
    return {'vertices': 180, 'triangles': 60, 'closed_edges': len(edges),
            'minimum_triangle_area_m2': minimum_area,
            'max_radial_m': max(math.hypot(p[0], p[2]) for p in data['vertices']),
            'axis_bounds_m': [min(p[1] for p in data['vertices']), max(p[1] for p in data['vertices'])]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'candidate-mesh.json')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    data = build()
    checks = validate(data)
    payload = (json.dumps(data, indent=2, sort_keys=True)+'\n').encode()
    if args.verify_only:
        assert args.output.read_bytes() == payload, 'candidate is not exact reconstruction'
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print(json.dumps({'output': str(args.output), 'sha256': hashlib.sha256(payload).hexdigest(),
                      'bytes': len(payload), 'geometry_checks': checks}, sort_keys=True))


if __name__ == '__main__':
    main()
