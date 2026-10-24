"""Read-only topology/texture/proxy inspection of selected official long01 files."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    vertices, uvs, faces, face_uvs = [], [], [], []
    for line in (a.input / 'long01.obj').read_text().splitlines():
        q = line.split()
        if not q:
            continue
        if q[0] == 'v': vertices.append(list(map(float, q[1:4])))
        elif q[0] == 'vt': uvs.append(list(map(float, q[1:3])))
        elif q[0] == 'f':
            faces.append([int(x.split('/')[0]) - 1 for x in q[1:]])
            face_uvs.append([int(x.split('/')[1]) - 1 for x in q[1:]])
    vertices, uvs = np.array(vertices), np.array(uvs)
    edges, adjacent = Counter(), defaultdict(set)
    for face in faces:
        for left, right in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((left, right)))] += 1
            adjacent[left].add(right)
            adjacent[right].add(left)
    remaining, components, members = set(range(len(vertices))), [], []
    while remaining:
        seed = min(remaining)
        queue, ids = [seed], set()
        remaining.remove(seed)
        while queue:
            vertex = queue.pop()
            ids.add(vertex)
            for other in adjacent[vertex]:
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
        selected_faces = [i for i, face in enumerate(faces) if face[0] in ids]
        points = vertices[sorted(ids)]
        components.append({'vertices': len(ids), 'faces': len(selected_faces),
                           'min': points.min(axis=0).tolist(), 'max': points.max(axis=0).tolist()})
        members.append((ids, selected_faces))
    texture = np.array(Image.open(a.input / 'long01_diffuse.png'))
    alpha = texture[:, :, 3]
    def sample(uv):
        x = min(alpha.shape[1] - 1, max(0, round(float(uv[0]) * (alpha.shape[1] - 1))))
        y = min(alpha.shape[0] - 1, max(0, round((1 - float(uv[1])) * (alpha.shape[0] - 1))))
        return int(alpha[y, x])
    largest = max(range(len(components)), key=lambda i: components[i]['faces'])
    # Inspect the upper third of this connected mesh in the source's Y-up axis.
    # Centroid samples are evidence about the source texture, not a full opacity proof.
    ids, face_ids = members[largest]
    minimum, maximum = vertices[sorted(ids), 1].min(), vertices[sorted(ids), 1].max()
    threshold = minimum + (maximum - minimum) * 2 / 3
    cap_faces = [i for i in face_ids if vertices[faces[i], 1].mean() >= threshold]
    cap_alpha = np.array([sample(uvs[face_uvs[i]].mean(axis=0)) for i in cap_faces])
    boundary = [edge for edge, count in edges.items() if count == 1]
    coefficients, fitting = [], False
    for line in (a.input / 'long01.mhclo').read_text().splitlines():
        if line.startswith('verts '):
            fitting = True
            continue
        if fitting and len(line.split()) == 9:
            try: coefficients.append(list(map(float, line.split()[3:6])))
            except ValueError: pass
    coefficients = np.array(coefficients)
    report = {
        'schema_version': 2, 'scope': 'Read-only existing source inspection; no new geometry, fit, native preview or runtime adoption',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'inputs': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(a.input.iterdir()) if path.is_file()},
        'mesh': {'vertices': len(vertices), 'uv_vertices': len(uvs), 'faces': len(faces),
                 'triangles_if_fanned': sum(len(f) - 2 for f in faces), 'face_sizes': dict(Counter(map(len, faces))),
                 'finite': bool(np.isfinite(vertices).all()), 'connected_components': components,
                 'boundary_edges': len(boundary), 'nonmanifold_edges_over_two_faces': sum(n > 2 for n in edges.values()),
                 'largest_component': largest, 'largest_component_vertex_ids': sorted(ids),
                 'largest_component_face_ids': face_ids,
                 'upper_third': {'source_y_threshold': float(threshold), 'sampled_face_centroids': len(cap_faces),
                                'alpha_min': int(cap_alpha.min()), 'alpha_max': int(cap_alpha.max()),
                                'alpha_ge243_fraction': float((cap_alpha >= 243).mean()),
                                'limit': 'Centroids only, not all covered texels; this does not establish a fully opaque cap in native rendering'}},
        'texture': {'dimensions': [alpha.shape[1], alpha.shape[0]], 'channels': texture.shape[2],
                    'alpha_min': int(alpha.min()), 'alpha_max': int(alpha.max()),
                    'entire_image_alpha_ge243_fraction': float((alpha >= 243).mean()),
                    'entire_image_alpha_ge128_fraction': float((alpha >= 128).mean())},
        'mhclo': {'basemesh': 'hm08', 'fitting_rows': len(coefficients),
                  'minimum_fitting_coefficient': float(coefficients.min()), 'maximum_fitting_coefficient': float(coefficients.max()),
                  'maximum_sum_error': float(abs(coefficients.sum(axis=1) - 1).max()),
                  'warning': 'Source barycentric/extrapolation coefficients are not skin joint weights. Canonical Rama GLB vertex order is not hm08.'},
    }
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'mesh'}, indent=2))
    print(json.dumps({'vertices': len(vertices), 'faces': len(faces), 'components': len(components),
                      'largest': components[largest], 'upper_third': report['mesh']['upper_third']}, indent=2))


if __name__ == '__main__':
    main()
