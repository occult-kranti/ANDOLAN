#!/usr/bin/env python3
"""Author seven broad upper-nape layers against the exact retained R7 hair."""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / 'art/hero-rama-lod'))
from glb_lod import GLB

SOURCE = PROJECT / 'assets/heroes/rama-hero.glb'
SOURCE_SHA = '8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c'


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    glb = GLB(SOURCE)
    primitive = glb.doc['meshes'][2]['primitives'][0]
    v = glb.array(primitive['attributes']['POSITION']).astype(float)
    tris = v[glb.array(primitive['indices']).reshape(-1, 3)]
    a = tris[:, 0]
    e1, e2 = tris[:, 1]-a, tris[:, 2]-a

    def outside(y, angle):
        origin = np.array([0., y, .025])
        direction = np.array([math.sin(angle), 0., math.cos(angle)])
        h = np.cross(direction, e2)
        det = (e1*h).sum(1)
        inv = np.divide(1., det, out=np.zeros_like(det), where=abs(det)>1e-12)
        s = origin-a
        u = (s*h).sum(1)*inv
        q = np.cross(s, e1)
        vv = (q*direction).sum(1)*inv
        distance = (e2*q).sum(1)*inv
        valid = (abs(det)>1e-12)&(u>=-1e-8)&(vv>=-1e-8)&(u+vv<=1+1e-8)&(distance>0)
        assert valid.any(), (y, angle)
        return origin + direction*distance[valid].max(), direction

    guides = []
    angles = [2.10, 2.42, 2.78, 3.14, 3.50, 3.86, 4.18]
    tips = [1.689, 1.702, 1.677, 1.713, 1.688, 1.697, 1.688]
    widths = [.015, .022, .024, .026, .023, .021, .016]
    for index, angle in enumerate(angles):
        points = []
        # An actual short overlapping tier; no sparse temple filaments. Root
        # meets the existing hair, then lifts by at most nine millimetres.
        for step, (y, relief) in enumerate(zip([1.797, 1.774, 1.735, tips[index]], [-.0005, .004, .007, .009])):
            sweep = (math.pi-angle)*.15*(step/3)
            point, direction = outside(y, angle+sweep)
            points.append((point+direction*relief).round(9).tolist())
        guides.append({'name': 'upper-layer-'+str(index), 'points': points,
                       'width': widths[index], 'depth': .0038 if index%2 else .0033,
                       'outward': [round(math.sin(angle), 9), 0., round(math.cos(angle), 9)]})
    document = {'schema': 1, 'source_glb': 'assets/heroes/rama-hero.glb',
                'source_sha256': SOURCE_SHA, 'generator': 'art/hero-finish/build_g2_hair_layers.py',
                'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'bone': 'head', 'segments': 16, 'sides': 8,
                'rights': 'Original authored YUGA layer guides fitted to original YUGA R7 groom.',
                'scope': 'Optional seven broad upper-nape layers. No lower-nape, eyebrow, topknot, rig or source GLB rewrite.',
                'guides': guides}
    output = PROJECT / 'assets/hero-finish/upper-hair-layers.json'
    output.write_text(json.dumps(document, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'output': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'guides': len(guides)}))


if __name__ == '__main__':
    main()
