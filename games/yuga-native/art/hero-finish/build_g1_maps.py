#!/usr/bin/env python3
"""Original periodic scalar PBR fields for the existing Rama UVs; no photo inputs."""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
OUTPUT = PROJECT / 'assets/hero-finish'
SIZE = 512


def hair(u, v):
    # U travels around each retained R7 clump; V follows its length. Separate
    # bundle and fibre frequencies break the old uniformly spaced ridges.
    turn = math.tau
    bundle = .052 * math.sin(turn * (5*u + .07*math.sin(turn*2*v)))
    bundle += .033 * math.sin(turn * (9*u - .06*math.sin(turn*3*v)))
    fibres = .024 * math.sin(turn * (53*u + .11*math.sin(turn*2*v)))
    fibres += .014 * math.sin(turn * (97*u - .08*math.sin(turn*5*v)))
    length = .012 * math.sin(turn*3*v)
    return min(.72, max(.43, .575 + bundle + fibres + length))


def gold(u, v):
    # Broad forged variation plus low-amplitude crossing tool marks. Existing
    # modeled ornament and original normal map supply relief, not this scalar.
    turn = math.tau
    forged = .029 * math.sin(turn*(3*u + 2*v)) * math.cos(turn*(2*u - 3*v))
    forged += .021 * math.sin(turn*(7*u - 5*v))
    marks = .013 * math.sin(turn*(61*u + 17*v))
    marks += .010 * math.sin(turn*(23*u - 71*v))
    return min(.50, max(.33, .415 + forged + marks))


def build(field):
    image = Image.new('L', (SIZE, SIZE))
    # Inclusive endpoints explicitly make both wrap edges byte-identical.
    image.putdata([round(255*field(x/(SIZE-1), y/(SIZE-1)))
                   for y in range(SIZE) for x in range(SIZE)])
    return image


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    for name, field in [('hair-bundle-roughness.png', hair), ('forged-gold-roughness.png', gold)]:
        image = build(field)
        path = OUTPUT / name
        image.save(path, compress_level=9, optimize=False)
        records.append({'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'bytes': path.stat().st_size, 'size': [SIZE, SIZE],
                        'range_u8': list(image.getextrema()), 'mode': image.mode,
                        'channel': 'RED', 'color_space': 'linear scalar',
                        'source': 'original analytic field in art/hero-finish/build_g1_maps.py'})
    manifest = {'schema': 1, 'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'generator_source': 'art/hero-finish/build_g1_maps.py',
                'maps': records, 'scope': 'Roughness only; original albedo, normals, UVs, geometry, rig and motion preserved.'}
    (OUTPUT / 'g1-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
